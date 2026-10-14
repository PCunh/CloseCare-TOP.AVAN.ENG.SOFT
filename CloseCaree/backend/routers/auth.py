
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Request,
    status
)

from pwdlib import PasswordHash
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas import (
    LoginDados,
    LoginResposta,
    UsuarioResposta
)

from security import (
    criar_token,
    obter_usuario_atual,
    COOKIE_NAME,
    COOKIE_SECURE,
    EXPIRATION_MINUTES
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

password_hash = PasswordHash.recommended()


def verificar_origem(request: Request):

    origens = {
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000"
    }

    origem = request.headers.get("origin")

    if origem and origem not in origens:
        raise HTTPException(
            status_code=403,
            detail="Origem não autorizada."
        )


@router.post(
    "/login",
    response_model=LoginResposta
)
def login(
    dados: LoginDados,
    response: Response,
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):

    verificar_origem(request)

    usuario = db.scalar(
        select(Usuario).where(
            func.lower(Usuario.email) == dados.email.lower()
        )
    )

    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha inválidos."
    )

    if usuario is None:
        raise erro_credenciais

    try:
        senha_correta = password_hash.verify(
            dados.senha,
            usuario.senha_hash
        )
    except (ValueError, TypeError):
        senha_correta = False

    if not senha_correta:
        raise erro_credenciais

    token = criar_token(usuario.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=EXPIRATION_MINUTES * 60,
        path="/"
    )

    return {
        "mensagem": "Login realizado com sucesso!",
        "usuario": usuario
    }


@router.get(
    "/me",
    response_model=UsuarioResposta
)
def consultar_usuario_atual(
    usuario: Annotated[
        Usuario,
        Depends(obter_usuario_atual)
    ]
):
    return usuario


@router.post("/logout")
def logout(
    response: Response,
    request: Request
):

    verificar_origem(request)

    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=COOKIE_SECURE,
        httponly=True
    )

    return {
        "mensagem": "Logout realizado com sucesso!"
    }
