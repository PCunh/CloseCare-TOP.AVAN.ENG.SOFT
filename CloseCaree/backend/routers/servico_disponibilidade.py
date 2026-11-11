
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from security import obter_usuario_atual
from components.erros import ErroRegra
from components.disponibilidade.service import DisponibilidadeService
from routers.disponibilidade_esbc import (
    Intervalo,
    HorarioSaida,
    exigir_profissional,
    origem_valida,
    executar
)

router = APIRouter(
    prefix="/servicos/disponibilidade",
    tags=["SOA - Serviço de Disponibilidade"]
)

@router.get(
    "/profissionais/{profissional_id}/horarios",
    response_model=list[HorarioSaida]
)
def consultar_horarios(
    profissional_id: int,
    db: Annotated[Session, Depends(get_db)],
    data: date | None = None
):
    try:
        return DisponibilidadeService(db).consultarHorarios(
            profissional_id, data
        )
    except ErroRegra as erro:
        raise HTTPException(erro.status_code, erro.mensagem)

@router.post(
    "/horarios",
    response_model=HorarioSaida,
    status_code=201
)
def cadastrar_horario(
    dados: Intervalo,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(obter_usuario_atual)]
):
    origem_valida(request)
    profissional = exigir_profissional(db, usuario)

    return executar(
        db,
        lambda: DisponibilidadeService(db).cadastrarHorario(
            profissional.id,
            dados.inicio,
            dados.fim
        )
    )

@router.put(
    "/horarios/{horario_id}",
    response_model=HorarioSaida
)
def atualizar_horario(
    horario_id: int,
    dados: Intervalo,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(obter_usuario_atual)]
):
    origem_valida(request)
    profissional = exigir_profissional(db, usuario)

    return executar(
        db,
        lambda: DisponibilidadeService(db).atualizarHorario(
            horario_id,
            profissional.id,
            dados.inicio,
            dados.fim
        )
    )

@router.delete(
    "/horarios/{horario_id}",
    status_code=204
)
def cancelar_horario(
    horario_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(obter_usuario_atual)]
):
    origem_valida(request)
    profissional = exigir_profissional(db, usuario)

    executar(
        db,
        lambda: DisponibilidadeService(db).removerDisponibilidade(
            horario_id,
            profissional.id
        )
    )
