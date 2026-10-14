
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    Index,
    text,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)

    nome: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False
    )

    senha_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    tipo_usuario: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "tipo_usuario IN ('paciente', 'profissional')",
            name="ck_tipo_usuario"
        ),
    )


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        unique=True,
        nullable=False
    )

    telefone: Mapped[str | None] = mapped_column(
        String(20)
    )

    endereco: Mapped[str | None] = mapped_column(
        String(255)
    )


class Profissional(Base):
    __tablename__ = "profissionais"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        unique=True,
        nullable=False
    )

    especialidade: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    raio_atendimento_km: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "raio_atendimento_km >= 0",
            name="ck_raio_atendimento"
        ),
    )


class Horario(Base):
    __tablename__ = "horarios"

    id: Mapped[int] = mapped_column(primary_key=True)

    profissional_id: Mapped[int] = mapped_column(
        ForeignKey("profissionais.id"),
        nullable=False
    )

    inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    fim: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "profissional_id",
            "inicio",
            name="uq_profissional_inicio"
        ),
        CheckConstraint(
            "fim > inicio",
            name="ck_horario_intervalo"
        ),
    )


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id: Mapped[int] = mapped_column(primary_key=True)

    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("pacientes.id"),
        nullable=False
    )

    horario_id: Mapped[int] = mapped_column(
        ForeignKey("horarios.id"),
        nullable=False
    )

    tipo: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="agendado",
        server_default="agendado",
        nullable=False
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('consulta', 'exame')",
            name="ck_tipo_agendamento"
        ),
        CheckConstraint(
            "status IN ('agendado', 'cancelado', 'realizado')",
            name="ck_status_agendamento"
        ),
        
        Index(
            "uq_horario_bloqueado",
            "horario_id",
            unique=True,
            postgresql_where=text(
                "status IN ('agendado', 'realizado')"
            )
        )
    ,
    )
