from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, Paciente, Horario
from security import obter_usuario_atual
from components.erros import ErroRegra
from components.disponibilidade.service import DisponibilidadeService
from components.agendamentos.service import AgendamentosService

router = APIRouter(prefix='/esbc/agendamentos', tags=['ESBC - Agendamentos'])
ORIGENS = {'http://localhost:5500', 'http://localhost:8000'}

class SolicitarAgendamento(BaseModel):
    horario_id: int = Field(gt=0)

class SolicitarRemarcacao(BaseModel):
    novo_horario_id: int = Field(gt=0)

class AgendamentoSaida(BaseModel):
    id: int
    paciente_id: int
    horario_id: int
    tipo: str
    status: str

def origem_valida(request: Request) -> None:
    if request.headers.get('origin') not in ORIGENS:
        raise HTTPException(403, 'Origem não autorizada.')

def paciente_autenticado(db: Session, usuario: Usuario) -> Paciente:
    if usuario.tipo_usuario != 'paciente':
        raise HTTPException(403, 'Somente pacientes podem executar esta operação.')
    perfil = db.scalar(select(Paciente).where(Paciente.usuario_id == usuario.id))
    if perfil is None:
        raise HTTPException(403, 'Perfil de paciente não encontrado.')
    return perfil

def servico(db: Session) -> AgendamentosService:
    return AgendamentosService(db, DisponibilidadeService(db))

def executar(db: Session, funcao):
    try:
        resultado = funcao()
        db.commit()
        return resultado
    except ErroRegra as erro:
        db.rollback()
        raise HTTPException(erro.status_code, erro.mensagem)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Horário indisponível.')

@router.post('', response_model=AgendamentoSaida, status_code=201)
def confirmar(dados: SolicitarAgendamento, request: Request, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    origem_valida(request)
    paciente = paciente_autenticado(db, usuario)
    return executar(db, lambda: servico(db).confirmarAgendamento(paciente.id, dados.horario_id))

@router.get('/meus', response_model=list[AgendamentoSaida])
def meus(db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    paciente = paciente_autenticado(db, usuario)
    return servico(db).listarAgendamentos(paciente.id)

@router.get('/{agendamento_id}', response_model=AgendamentoSaida)
def detalhes(agendamento_id: int, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    paciente = paciente_autenticado(db, usuario)
    try:
        return servico(db).consultarDetalhes(agendamento_id, paciente.id)
    except ErroRegra as erro:
        raise HTTPException(erro.status_code, erro.mensagem)

@router.patch('/{agendamento_id}/cancelar', response_model=AgendamentoSaida)
def cancelar(agendamento_id: int, request: Request, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    origem_valida(request)
    paciente = paciente_autenticado(db, usuario)
    return executar(db, lambda: servico(db).cancelarAgendamento(agendamento_id, paciente.id))

@router.patch('/{agendamento_id}/remarcar', response_model=AgendamentoSaida)
def remarcar(agendamento_id: int, dados: SolicitarRemarcacao, request: Request, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(obter_usuario_atual)]):
    origem_valida(request)
    paciente = paciente_autenticado(db, usuario)
    return executar(db, lambda: servico(db).remarcarAgendamento(agendamento_id, dados.novo_horario_id, paciente.id))
