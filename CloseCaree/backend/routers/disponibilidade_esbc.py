from datetime import date, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Usuario, Profissional, Horario, Agendamento
from security import obter_usuario_atual
from components.erros import ErroRegra
from components.disponibilidade.service import DisponibilidadeService

router = APIRouter(prefix='/esbc/disponibilidade', tags=['ESBC - Disponibilidade'])
ORIGENS = {'http://localhost:5500', 'http://localhost:8000'}

class Intervalo(BaseModel):
    inicio: datetime
    fim: datetime

class HorarioSaida(BaseModel):
    id: int
    profissional_id: int
    inicio: datetime
    fim: datetime

def exigir_profissional(db: Session, usuario: Usuario) -> Profissional:
    if usuario.tipo_usuario != 'profissional':
        raise HTTPException(403, 'Somente profissionais podem gerenciar horários.')
    perfil = db.scalar(select(Profissional).where(Profissional.usuario_id == usuario.id))
    if perfil is None:
        raise HTTPException(403, 'Perfil de profissional não encontrado.')
    return perfil

def origem_valida(request: Request) -> None:
    if request.headers.get('origin') not in ORIGENS:
        raise HTTPException(403, 'Origem não autorizada.')

def executar(db, funcao):
    try:
        resultado = funcao()
        db.commit()
        return resultado
    except ErroRegra as erro:
        db.rollback()
        raise HTTPException(erro.status_code, erro.mensagem)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Conflito ao salvar horário.')


@router.get('/profissionais')
def profissionais_disponiveis(db: Annotated[Session, Depends(get_db)]):
    from models import Profissional, Usuario
    registros = db.execute(select(Profissional, Usuario).join(Usuario, Profissional.usuario_id == Usuario.id).order_by(Usuario.nome)).all()
    return [{'id': p.id, 'nome': u.nome, 'especialidade': p.especialidade} for p, u in registros]

@router.get('/meus')
def meus_horarios(db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    perfil = exigir_profissional(db, usuario)
    from models import Horario, Agendamento
    horarios = list(db.scalars(select(Horario).where(Horario.profissional_id == perfil.id).order_by(Horario.inicio)))
    agendamentos = db.execute(select(Agendamento.horario_id, Agendamento.status).where(Agendamento.horario_id.in_([h.id for h in horarios]))).all() if horarios else []
    statuses = {}
    for horario_id, status in agendamentos:
        if status in ('agendado', 'realizado'):
            statuses[horario_id] = status
    return [{'id': h.id, 'profissional_id': h.profissional_id, 'inicio': h.inicio, 'fim': h.fim, 'status': statuses.get(h.id, 'livre')} for h in horarios]

@router.get('/{profissional_id}', response_model=list[HorarioSaida])
def listar(profissional_id: int, db: Annotated[Session, Depends(get_db)], data: date | None = None):
    try:
        return DisponibilidadeService(db).consultarHorarios(profissional_id, data)
    except ErroRegra as erro:
        raise HTTPException(erro.status_code, erro.mensagem)

@router.post('', response_model=HorarioSaida, status_code=201)
def cadastrar(dados: Intervalo, request: Request, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    origem_valida(request)
    perfil = exigir_profissional(db, usuario)
    servico = DisponibilidadeService(db)
    return executar(db, lambda: servico.cadastrarHorario(perfil.id, dados.inicio, dados.fim))

@router.put('/{horario_id}', response_model=HorarioSaida)
def atualizar(horario_id: int, dados: Intervalo, request: Request, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    origem_valida(request)
    perfil = exigir_profissional(db, usuario)
    servico = DisponibilidadeService(db)
    return executar(db, lambda: servico.atualizarHorario(horario_id, perfil.id, dados.inicio, dados.fim))

@router.delete('/{horario_id}', status_code=204)
def remover(horario_id: int, request: Request, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    origem_valida(request)
    perfil = exigir_profissional(db, usuario)
    servico = DisponibilidadeService(db)
    executar(db, lambda: servico.removerDisponibilidade(horario_id, perfil.id))
