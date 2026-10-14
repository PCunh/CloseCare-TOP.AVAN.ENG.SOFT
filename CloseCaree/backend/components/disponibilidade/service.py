from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Profissional, Horario, Agendamento
from components.erros import ErroRegra

FUSO = ZoneInfo('America/Sao_Paulo')
BLOQUEANTES = ('agendado', 'realizado')

class DisponibilidadeService:
    def __init__(self, db: Session):
        self.db = db

    def _validar_intervalo(self, inicio: datetime, fim: datetime) -> None:
        if inicio.tzinfo is None or fim.tzinfo is None:
            raise ErroRegra(422, 'Informe datas e horas com fuso horário.')
        if inicio <= datetime.now(timezone.utc) or fim <= inicio:
            raise ErroRegra(422, 'Intervalo inválido ou no passado.')

    def _ocupado(self, horario_id: int) -> bool:
        return self.db.scalar(select(Agendamento.id).where(
            Agendamento.horario_id == horario_id,
            Agendamento.status.in_(BLOQUEANTES)
        ).limit(1)) is not None

    def consultarHorarios(self, profissional_id: int, data: date | None = None) -> list[Horario]:
        if self.db.get(Profissional, profissional_id) is None:
            raise ErroRegra(404, 'Profissional não encontrado.')
        ocupado = select(Agendamento.id).where(
            Agendamento.horario_id == Horario.id,
            Agendamento.status.in_(BLOQUEANTES)
        ).exists()
        stmt = select(Horario).where(
            Horario.profissional_id == profissional_id,
            Horario.inicio > datetime.now(timezone.utc),
            ~ocupado
        )
        if data is not None:
            inicio_dia = datetime.combine(data, time.min, tzinfo=FUSO)
            stmt = stmt.where(Horario.inicio >= inicio_dia, Horario.inicio < inicio_dia + timedelta(days=1))
        return list(self.db.scalars(stmt.order_by(Horario.inicio)))

    def verificarDisponibilidade(self, horario_id: int) -> bool:
        horario = self.db.get(Horario, horario_id)
        return horario is not None and horario.inicio > datetime.now(timezone.utc) and not self._ocupado(horario_id)

    def validarHorarioParaReserva(self, horario_id: int) -> Horario:
        horario = self.db.scalar(select(Horario).where(Horario.id == horario_id).with_for_update())
        if horario is None:
            raise ErroRegra(404, 'Horário não encontrado.')
        if horario.inicio <= datetime.now(timezone.utc):
            raise ErroRegra(409, 'Horário já iniciado.')
        if self._ocupado(horario.id):
            raise ErroRegra(409, 'Horário indisponível.')
        return horario

    def _bloquear_profissional(self, profissional_id: int) -> None:
        if self.db.scalar(select(Profissional.id).where(Profissional.id == profissional_id).with_for_update()) is None:
            raise ErroRegra(404, 'Profissional não encontrado.')

    def _verificar_sobreposicao(self, profissional_id: int, inicio: datetime, fim: datetime, ignorar_id: int | None = None) -> None:
        stmt = select(Horario.id).where(
            Horario.profissional_id == profissional_id,
            Horario.inicio < fim,
            Horario.fim > inicio
        )
        if ignorar_id is not None:
            stmt = stmt.where(Horario.id != ignorar_id)
        if self.db.scalar(stmt.limit(1)) is not None:
            raise ErroRegra(409, 'Há um horário sobreposto.')

    def cadastrarHorario(self, profissional_id: int, inicio: datetime, fim: datetime) -> Horario:
        self._validar_intervalo(inicio, fim)
        self._bloquear_profissional(profissional_id)
        self._verificar_sobreposicao(profissional_id, inicio, fim)
        horario = Horario(profissional_id=profissional_id, inicio=inicio, fim=fim)
        self.db.add(horario)
        self.db.flush()
        return horario

    def atualizarHorario(self, horario_id: int, profissional_id: int, inicio: datetime, fim: datetime) -> Horario:
        self._validar_intervalo(inicio, fim)
        self._bloquear_profissional(profissional_id)
        horario = self.db.scalar(select(Horario).where(
            Horario.id == horario_id, Horario.profissional_id == profissional_id
        ).with_for_update())
        if horario is None:
            raise ErroRegra(404, 'Horário não encontrado.')
        if self.db.scalar(select(Agendamento.id).where(Agendamento.horario_id == horario_id).limit(1)) is not None:
            raise ErroRegra(409, 'Horário com histórico de reserva não pode ser alterado.')
        self._verificar_sobreposicao(profissional_id, inicio, fim, horario_id)
        horario.inicio, horario.fim = inicio, fim
        self.db.flush()
        return horario

    def removerDisponibilidade(self, horario_id: int, profissional_id: int) -> None:
        self._bloquear_profissional(profissional_id)
        horario = self.db.scalar(select(Horario).where(
            Horario.id == horario_id, Horario.profissional_id == profissional_id
        ).with_for_update())
        if horario is None:
            raise ErroRegra(404, 'Horário não encontrado.')
        if self.db.scalar(select(Agendamento.id).where(Agendamento.horario_id == horario_id).limit(1)) is not None:
            raise ErroRegra(409, 'Horário com histórico de reserva não pode ser removido.')
        self.db.delete(horario)
        self.db.flush()
