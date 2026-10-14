
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from database import get_db
from models import Usuario, Paciente, Profissional
from schemas import UsuarioCriar, UsuarioResposta


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

password_hash = PasswordHash.recommended()


@router.post(
    "",
    response_model=UsuarioResposta,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_usuario(
    dados: UsuarioCriar,
    db: Annotated[Session, Depends(get_db)]
):

    if dados.tipo_usuario == "profissional":
        if not dados.especialidade:
            raise HTTPException(
                status_code=422,
                detail="Especialidade é obrigatória para profissionais."
            )

    usuario_existente = db.scalar(
        select(Usuario).where(
            func.lower(Usuario.email) == dados.email.lower()
        )
    )

    if usuario_existente:
        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado."
        )

    senha_protegida = password_hash.hash(dados.senha)

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        senha_hash=senha_protegida,
        tipo_usuario=dados.tipo_usuario
    )

    try:
        db.add(novo_usuario)

        db.flush()

        if dados.tipo_usuario == "paciente":

            novo_paciente = Paciente(
                usuario_id=novo_usuario.id,
                telefone=dados.telefone,
                endereco=dados.endereco
            )

            db.add(novo_paciente)

        elif dados.tipo_usuario == "profissional":

            novo_profissional = Profissional(
                usuario_id=novo_usuario.id,
                especialidade=dados.especialidade,
                raio_atendimento_km=(
                    dados.raio_atendimento_km
                    if dados.raio_atendimento_km is not None
                    else 10
                )
            )

            db.add(novo_profissional)

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Não foi possível concluir o cadastro. Verifique se o e-mail já está em uso."
        )

    db.refresh(novo_usuario)

    return novo_usuario
