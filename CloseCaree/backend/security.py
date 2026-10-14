
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt

from dotenv import load_dotenv
from fastapi import Cookie, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

EXPIRATION_MINUTES = int(
    os.getenv("JWT_EXPIRATION_MINUTES", "30")
)

COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)

COOKIE_NAME = "closecare_access_token"


if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Configure uma JWT_SECRET_KEY segura no arquivo .env"
    )

def criar_token(usuario_id: int):

    agora = datetime.now(timezone.utc)

    expiracao = agora + timedelta(
        minutes=EXPIRATION_MINUTES
    )

    conteudo = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": expiracao,
        "iss": "closecare"
    }

    token = jwt.encode(
        conteudo,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token

def obter_usuario_atual(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[
        str | None,
        Cookie(alias=COOKIE_NAME)
    ] = None
):

    erro_autenticacao = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuário não autenticado."
    )

    if not token:
        raise erro_autenticacao

    try:
        conteudo = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer="closecare",
            options={
                "require": ["sub", "exp", "iat", "iss"]
            }
        )

        usuario_id = int(conteudo["sub"])

    except (InvalidTokenError, ValueError, TypeError):
        raise erro_autenticacao

    usuario = db.get(Usuario, usuario_id)

    if usuario is None:
        raise erro_autenticacao

    return usuario
