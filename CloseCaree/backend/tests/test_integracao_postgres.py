import os
import secrets
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from database import engine, DB_NAME
from models import Usuario, Paciente, Profissional, Horario, Agendamento
from components.disponibilidade.service import DisponibilidadeService
from components.agendamentos.service import AgendamentosService
from components.erros import ErroRegra

pytestmark = pytest.mark.skipif(
    os.environ.get('CLOSECARE_TEST_DB') != '1' or not DB_NAME.endswith('_test'),
    reason='Use CLOSECARE_TEST_DB=1 e DB_NAME terminado em _test'
)


def test_ciclo_disponibilidade_agendamento_cancelamento():
    marca = secrets.token_hex(8)
    ids_usuarios = []
    ids_horarios = []
    ids_agendamentos = []
    try:
        with Session(engine) as db:
            profissional_usuario = Usuario(nome='ESBC Profissional', email=f'esbc-prof-{marca}@example.com', senha_hash='nao-utilizar-login', tipo_usuario='profissional')
            paciente_usuario = Usuario(nome='ESBC Paciente', email=f'esbc-pac-{marca}@example.com', senha_hash='nao-utilizar-login', tipo_usuario='paciente')
            db.add_all([profissional_usuario, paciente_usuario])
            db.flush()
            ids_usuarios = [profissional_usuario.id, paciente_usuario.id]
            perfil_prof = Profissional(usuario_id=profissional_usuario.id, especialidade='Enfermagem', raio_atendimento_km=10)
            perfil_pac = Paciente(usuario_id=paciente_usuario.id)
            db.add_all([perfil_prof, perfil_pac])
            db.flush()
            disponibilidade = DisponibilidadeService(db)
            agenda = AgendamentosService(db, disponibilidade)
            inicio = datetime.now(timezone.utc) + timedelta(days=30, minutes=secrets.randbelow(120))
            horario = disponibilidade.cadastrarHorario(perfil_prof.id, inicio, inicio + timedelta(hours=1))
            ids_horarios.append(horario.id)
            assert disponibilidade.verificarDisponibilidade(horario.id)
            assert len(disponibilidade.consultarHorarios(perfil_prof.id)) >= 1
            agendamento = agenda.confirmarAgendamento(perfil_pac.id, horario.id)
            ids_agendamentos.append(agendamento.id)
            assert not disponibilidade.verificarDisponibilidade(horario.id)
            with pytest.raises(ErroRegra) as erro:
                agenda.confirmarAgendamento(perfil_pac.id, horario.id)
            assert erro.value.status_code == 409
            agenda.cancelarAgendamento(agendamento.id, perfil_pac.id)
            assert disponibilidade.verificarDisponibilidade(horario.id)
            db.commit()
    finally:
        with Session(engine) as db, db.begin():
            if ids_agendamentos:
                db.execute(delete(Agendamento).where(Agendamento.id.in_(ids_agendamentos)))
            if ids_horarios:
                db.execute(delete(Horario).where(Horario.id.in_(ids_horarios)))
            if ids_usuarios:
                db.execute(delete(Paciente).where(Paciente.usuario_id.in_(ids_usuarios)))
                db.execute(delete(Profissional).where(Profissional.usuario_id.in_(ids_usuarios)))
                db.execute(delete(Usuario).where(Usuario.id.in_(ids_usuarios)))
