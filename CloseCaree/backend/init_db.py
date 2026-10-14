
from sqlalchemy import text

from database import engine, Base

import models


def inicializar_banco():
    print("Testando conexão com PostgreSQL...")

    with engine.connect() as conexao:
        resultado = conexao.execute(text("SELECT 1"))
        print("Conexão estabelecida:", resultado.scalar())

    print("Criando tabelas...")

    Base.metadata.create_all(bind=engine)

    print("Tabelas criadas ou já existentes:")
    for tabela in Base.metadata.sorted_tables:
        print("-", tabela.name)

    print("Banco Close Care inicializado com sucesso!")


if __name__ == "__main__":
    inicializar_banco()
