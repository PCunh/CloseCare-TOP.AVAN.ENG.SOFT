from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from components.erros import ErroRegra
from components.agendamentos.service import AgendamentosService
from components.disponibilidade.service import DisponibilidadeService


def test_agendamentos_requer_interface_disponibilidade():
    db = Mock()
    db.flush = Mock()
    disponibilidade = Mock()
    disponibilidade.validarHorarioParaReserva.return_value = SimpleNamespace(id=10)
    servico = AgendamentosService(db, disponibilidade)
    novo = servico.confirmarAgendamento(7, 10)
    disponibilidade.validarHorarioParaReserva.assert_called_once_with(10)
    assert novo.paciente_id == 7
    assert novo.horario_id == 10
    assert novo.status == 'agendado'
    db.add.assert_called_once()


def test_agendamentos_nao_salva_quando_indisponivel():
    db = Mock()
    disponibilidade = Mock()
    disponibilidade.validarHorarioParaReserva.side_effect = ErroRegra(409, 'Horário indisponível.')
    servico = AgendamentosService(db, disponibilidade)
    with pytest.raises(ErroRegra) as erro:
        servico.confirmarAgendamento(7, 10)
    assert erro.value.status_code == 409
    db.add.assert_not_called()


def test_disponibilidade_rejeita_intervalo_passado():
    servico = DisponibilidadeService(Mock())
    agora = datetime.now(timezone.utc)
    with pytest.raises(ErroRegra) as erro:
        servico.cadastrarHorario(1, agora - timedelta(hours=2), agora - timedelta(hours=1))
    assert erro.value.status_code == 422


def test_disponibilidade_rejeita_intervalo_invertido():
    servico = DisponibilidadeService(Mock())
    inicio = datetime.now(timezone.utc) + timedelta(days=1)
    with pytest.raises(ErroRegra) as erro:
        servico.cadastrarHorario(1, inicio + timedelta(hours=1), inicio)
    assert erro.value.status_code == 422
