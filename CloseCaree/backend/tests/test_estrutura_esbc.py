from pathlib import Path

BASE = Path(__file__).resolve().parents[2]

def test_telas_de_demonstracao():
    assert (BASE / "frontend" / "index.html").exists()
    assert (BASE / "frontend" / "app.js").exists()
    assert (BASE / "frontend" / "style.css").exists()

def test_interfaces_separadas():
    base = BASE / "backend" / "components"
    assert (base / "disponibilidade" / "interface.py").exists()
    assert (base / "agendamentos" / "interface.py").exists()

def test_integracao_por_interface():
    codigo = (BASE / "backend" / "components" / "agendamentos" / "service.py").read_text(encoding="utf-8")
    assert "IDisponibilidade" in codigo
    assert "self.disponibilidade.validarHorarioParaReserva" in codigo
