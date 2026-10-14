from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Agendamento, Horario
from components.disponibilidade.interface import IDisponibilidade
from components.erros import ErroRegra

class AgendamentosService:
    def __init__(self, db: Session, disponibilidade: IDisponibilidade):
        self.db = db
        self.disponibilidade = disponibilidade

    def confirmarAgendamento(self, paciente_id: int, horario_id: int) -> Agendamento:
        self.disponibilidade.validarHorarioParaReserva(horario_id)
        agendamento = Agendamento(paciente_id=paciente_id, horario_id=horario_id, tipo='consulta', status='agendado')
        self.db.add(agendamento)
        self.db.flush()
        return agendamento

    def listarAgendamentos(self, paciente_id: int) -> list[Agendamento]:
        return list(self.db.scalars(select(Agendamento).where(
            Agendamento.paciente_id == paciente_id
        ).order_by(Agendamento.id.desc())))

    def consultarDetalhes(self, agendamento_id: int, paciente_id: int) -> Agendamento:
        agendamento = self.db.scalar(select(Agendamento).where(
            Agendamento.id == agendamento_id, Agendamento.paciente_id == paciente_id
        ))
        if agendamento is None:
            raise ErroRegra(404, 'Agendamento não encontrado.')
        return agendamento

    def cancelarAgendamento(self, agendamento_id: int, paciente_id: int) -> Agendamento:
        atual = self.consultarDetalhes(agendamento_id, paciente_id)
        horario = self.db.scalar(select(Horario).where(Horario.id == atual.horario_id).with_for_update())
        agendamento = self.db.scalar(select(Agendamento).where(
            Agendamento.id == agendamento_id, Agendamento.paciente_id == paciente_id
        ).with_for_update())
        if agendamento.status != 'agendado' or horario.inicio <= datetime.now(timezone.utc):
            raise ErroRegra(409, 'Agendamento não pode ser cancelado.')
        agendamento.status = 'cancelado'
        self.db.flush()
        return agendamento

    def remarcarAgendamento(self, agendamento_id: int, novo_horario_id: int, paciente_id: int) -> Agendamento:
        atual = self.consultarDetalhes(agendamento_id, paciente_id)
        if atual.horario_id == novo_horario_id:
            raise ErroRegra(409, 'Novo horário deve ser diferente.')
        ids = sorted((atual.horario_id, novo_horario_id))
        horarios = list(self.db.scalars(select(Horario).where(Horario.id.in_(ids)).order_by(Horario.id).with_for_update()))
        if len(horarios) != 2:
            raise ErroRegra(404, 'Horário não encontrado.')
        origem = next(h for h in horarios if h.id == atual.horario_id)
        if atual.status != 'agendado' or origem.inicio <= datetime.now(timezone.utc):
            raise ErroRegra(409, 'Agendamento não pode ser remarcado.')
        destino = next(h for h in horarios if h.id == novo_horario_id)
        if origem.profissional_id != destino.profissional_id:
            raise ErroRegra(409, 'Remarcação permitida somente para o mesmo profissional.')
        self.disponibilidade.validarHorarioParaReserva(novo_horario_id)
        atual.horario_id = novo_horario_id
        self.db.flush()
        return atual
