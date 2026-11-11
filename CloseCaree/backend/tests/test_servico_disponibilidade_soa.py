
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base
from models import Usuario, Profissional, Horario, Agendamento, Paciente
from components.erros import ErroRegra
from components.disponibilidade.service import DisponibilidadeService


@pytest.fixture
def banco():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        usuario = Usuario(
            nome="Profissional Teste",
            email="prof@example.com",
            senha_hash="hash",
            tipo_usuario="profissional"
        )
        db.add(usuario)
        db.flush()

        profissional = Profissional(
            usuario_id=usuario.id,
            especialidade="Clínico"
        )
        db.add(profissional)
        db.commit()

        yield db, profissional.id

    engine.dispose()


def intervalo(dias=4, horas=0):
    inicio = (
        datetime.now(timezone.utc)
        .replace(minute=0, second=0, microsecond=0)
        + timedelta(days=dias, hours=horas)
    )

    return inicio, inicio + timedelta(hours=1)


def test_cadastrar_horario_com_sucesso(banco):
    db, pid = banco
    inicio, fim = intervalo()

    horario = DisponibilidadeService(db).cadastrarHorario(
        pid, inicio, fim
    )
    db.commit()

    assert horario.id is not None
    assert db.get(Horario, horario.id).profissional_id == pid


def test_cadastrar_horario_sobreposto_retorna_409(banco):
    db, pid = banco
    inicio, fim = intervalo()
    servico = DisponibilidadeService(db)

    servico.cadastrarHorario(pid, inicio, fim)
    db.commit()

    with pytest.raises(ErroRegra) as erro:
        servico.cadastrarHorario(
            pid,
            inicio + timedelta(minutes=30),
            fim + timedelta(minutes=30)
        )

    assert erro.value.status_code == 409


def test_atualizar_horario_com_sucesso(banco):
    db, pid = banco
    inicio, fim = intervalo()
    servico = DisponibilidadeService(db)

    horario = servico.cadastrarHorario(pid, inicio, fim)
    db.commit()

    novo_inicio, novo_fim = intervalo(dias=5)

    atualizado = servico.atualizarHorario(
        horario.id, pid, novo_inicio, novo_fim
    )
    db.commit()

    assert (
        atualizado.inicio.replace(tzinfo=None)
        == novo_inicio.replace(tzinfo=None)
    )


def test_atualizar_horario_com_reserva_retorna_409(banco):
    db, pid = banco
    servico = DisponibilidadeService(db)
    inicio, fim = intervalo()

    horario = servico.cadastrarHorario(pid, inicio, fim)

    paciente_usuario = Usuario(
        nome="Paciente Teste",
        email="pac@example.com",
        senha_hash="hash",
        tipo_usuario="paciente"
    )
    db.add(paciente_usuario)
    db.flush()

    paciente = Paciente(usuario_id=paciente_usuario.id)
    db.add(paciente)
    db.flush()

    db.add(
        Agendamento(
            paciente_id=paciente.id,
            horario_id=horario.id,
            tipo="consulta",
            status="agendado"
        )
    )
    db.commit()

    novo_inicio, novo_fim = intervalo(dias=5)

    with pytest.raises(ErroRegra) as erro:
        servico.atualizarHorario(
            horario.id, pid, novo_inicio, novo_fim
        )

    assert erro.value.status_code == 409


def test_cancelar_horario_livre(banco):
    db, pid = banco
    servico = DisponibilidadeService(db)
    inicio, fim = intervalo()

    horario = servico.cadastrarHorario(pid, inicio, fim)
    db.commit()

    horario_id = horario.id

    servico.removerDisponibilidade(horario_id, pid)
    db.commit()

    assert db.get(Horario, horario_id) is None


def test_cancelar_horario_inexistente_retorna_404(banco):
    db, pid = banco

    with pytest.raises(ErroRegra) as erro:
        DisponibilidadeService(db).removerDisponibilidade(
            999999, pid
        )

    assert erro.value.status_code == 404
