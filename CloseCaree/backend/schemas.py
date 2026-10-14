
from typing import Literal

from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator
)
class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=3, max_length=150)

    email: EmailStr

    senha: str = Field(min_length=8, max_length=128)

    tipo_usuario: Literal["paciente", "profissional"]

    telefone: str | None = Field(
        default=None,
        max_length=20
    )

    endereco: str | None = Field(
        default=None,
        max_length=255
    )

    especialidade: str | None = Field(
        default=None,
        max_length=100
    )

    raio_atendimento_km: int | None = Field(
        default=None,
        ge=0,
        le=500
    )

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor):
        valor = valor.strip()

        if len(valor) < 3:
            raise ValueError("Nome deve ter pelo menos 3 caracteres")

        return valor

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor):
        return str(valor).lower()

    @field_validator("especialidade")
    @classmethod
    def validar_especialidade(cls, valor):
        if valor is not None:
            valor = valor.strip()

            if not valor:
                return None

        return valor

class UsuarioResposta(BaseModel):
    id: int
    nome: str
    email: EmailStr
    tipo_usuario: Literal["paciente", "profissional"]

    model_config = ConfigDict(from_attributes=True)

class LoginDados(BaseModel):
    email: EmailStr
    senha: str


class LoginResposta(BaseModel):
    mensagem: str
    usuario: UsuarioResposta

    
class ProfissionalResumo(BaseModel):
    id: int
    nome: str
    especialidade: str
    raio_atendimento_km: int

class HorarioDisponivel(BaseModel):
    id: int
    profissional_id: int
    inicio: datetime
    fim: datetime

    model_config = ConfigDict(from_attributes=True)

class AgendamentoCriar(BaseModel):
    horario_id: int = Field(gt=0)


class AgendamentoResposta(BaseModel):
    id: int
    horario_id: int
    profissional_id: int
    tipo: str
    status: str
    inicio: datetime
    fim: datetime


class AgendamentoDetalhe(BaseModel):
    id: int
    horario_id: int
    profissional_id: int
    profissional_nome: str
    especialidade: str
    tipo: str
    status: str
    inicio: datetime
    fim: datetime
    criado_em: datetime
