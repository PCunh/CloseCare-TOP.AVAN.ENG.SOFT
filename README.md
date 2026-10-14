# CloseCare-TOP.AVAN.ENG.SOFT
CloseCare, gerenciamento de atendimentos domiciliares. O projeto permite que profissionais disponibilizem horários e que pacientes consultem horários livres, agendem consultas, visualizem seus agendamentos, cancelem ou remarquem consultas. A implementação enfatiza a separação de responsabilidades por componentes no estilo **ESBC (Enterprise Service Bus Components)**, com interfaces explícitas entre os serviços de disponibilidade e agendamento.

## Tecnologias utilizadas
### Backend
- **Python 3.10+**: linguagem da API e das regras de negócio.
- **FastAPI**: criação dos endpoints REST e documentação automática da API.
- **Uvicorn**: servidor ASGI para executar a aplicação.
- **SQLAlchemy 2**: mapeamento objeto-relacional e acesso ao banco.
- **PostgreSQL**: persistência de usuários, perfis, horários e agendamentos.
- **Psycopg 3**: driver de conexão com PostgreSQL.
- **Pydantic**: validação dos dados de entrada e saída.
- **PyJWT**: criação e validação dos tokens JWT.
- **pwdlib com Argon2**: hash e verificação de senhas.
- **python-dotenv**: leitura das configurações do arquivo `.env`.
- **pytest e httpx**: infraestrutura para testes.

### Frontend
- **HTML5**: estrutura das telas.
- **CSS3**: estilos e apresentação visual.
- **JavaScript (Fetch API)**: interação com a API REST e atualização dos painéis.

## estrutura dos componentes

```text
CloseCare/
├── backend/
│   ├── main.py                       # Inicialização da API FastAPI e CORS
│   ├── database.py                   # Configuração da conexão e sessões do banco
│   ├── init_db.py                    # Criação das tabelas
│   ├── models.py                     # Modelos ORM
│   ├── schemas.py                    # Schemas e validação de dados
│   ├── security.py                   # JWT e identificação do usuário autenticado
│   ├── requirements.txt              # Dependências Python
│   ├── .env.example                  # Modelo de configuração
│   ├── routers/
│   │   ├── auth.py                   # Login, sessão e logout
│   │   ├── usuarios.py                # Cadastro de usuários
│   │   ├── disponibilidade_esbc.py    # Endpoints de disponibilidade
│   │   └── agendamentos_esbc.py       # Endpoints de agendamento
│   ├── components/
│      ├── erros.py                   # Erros de regra de negócio
│      ├── disponibilidade/
│      │   ├── interface.py           # Contrato IDisponibilidade
│      │   └── service.py             # Regras de disponibilidade
│      └── agendamentos/
│          ├── interface.py           # Contrato IAgendamentos
│          └── service.py             # Regras de agendamento   
└── frontend/
    ├── index.html                     # Interface principal
    ├── app.js                         # Lógica da interface e chamadas HTTP
    └── css/
        └── style.css                  # Estilos da aplicação
```


## interfaces e operações implementadas

### Interfaces de componentes

A interface `IDisponibilidade`, definida em `components/disponibilidade/interface.py`, declara as operações:

- `consultarHorarios(profissional_id, data=None)`
- `verificarDisponibilidade(horario_id)`
- `validarHorarioParaReserva(horario_id)`
- `cadastrarHorario(profissional_id, inicio, fim)`
- `atualizarHorario(horario_id, profissional_id, inicio, fim)`
- `removerDisponibilidade(horario_id, profissional_id)`

A interface `IAgendamentos`, definida em `components/agendamentos/interface.py`, declara:

- `confirmarAgendamento(paciente_id, horario_id)`
- `listarAgendamentos(paciente_id)`
- `consultarDetalhes(agendamento_id, paciente_id)`
- `cancelarAgendamento(agendamento_id, paciente_id)`
- `remarcarAgendamento(agendamento_id, novo_horario_id, paciente_id)`

### API HTTP

| Método | Rota | Operação |
|---|---|---|
| `GET` | `/health` | Verifica se a API está ativa. |
| `POST` | `/usuarios` | Cadastra um paciente ou profissional. |
| `POST` | `/auth/login` | Autentica o usuário e cria a sessão. |
| `GET` | `/auth/me` | Retorna o usuário autenticado. |
| `POST` | `/auth/logout` | Encerra a sessão removendo o cookie. |
| `GET` | `/esbc/disponibilidade/profissionais` | Lista os profissionais cadastrados. |
| `GET` | `/esbc/disponibilidade/meus` | Lista os horários do profissional autenticado. |
| `GET` | `/esbc/disponibilidade/{profissional_id}` | Consulta horários livres de um profissional; aceita o parâmetro opcional `data`. |
| `POST` | `/esbc/disponibilidade` | Cadastra um horário para o profissional autenticado. |
| `PUT` | `/esbc/disponibilidade/{horario_id}` | Atualiza um horário permitido. |
| `DELETE` | `/esbc/disponibilidade/{horario_id}` | Remove uma disponibilidade sem histórico de reserva. |
| `POST` | `/esbc/agendamentos` | Confirma um agendamento para o paciente autenticado. |
| `GET` | `/esbc/agendamentos/meus` | Lista os agendamentos do paciente autenticado. |
| `GET` | `/esbc/agendamentos/{agendamento_id}` | Consulta os detalhes de um agendamento do paciente. |
| `PATCH` | `/esbc/agendamentos/{agendamento_id}/cancelar` | Cancela um agendamento permitido. |
| `PATCH` | `/esbc/agendamentos/{agendamento_id}/remarcar` | Remarca para outro horário livre do mesmo profissional. |

A documentação interativa gerada pelo FastAPI fica disponível em `/docs` quando o backend está em execução.

### Operações disponíveis na interface

- Cadastro e login de pacientes e profissionais, além de logout.
- Para profissionais: cadastrar horários, consultar a própria lista, atualizar e excluir horários elegíveis.
- Para pacientes: listar profissionais, consultar horários livres, agendar, listar consultas, cancelar e remarcar agendamentos.
- Exibição de mensagens de sucesso e erro retornadas pela API.

## instruções para execução

### Pré-requisitos
- Python instalado.
- PostgreSQL instalado e em execução.
- Um banco de dados e usuário PostgreSQL com permissão para criar tabelas.
- Um terminal na pasta do projeto.

### Configurar o banco e as variáveis de ambiente

1. Crie um banco PostgreSQL (por exemplo, `closecare`) e um usuário com permissões sobre ele.
2. Entre na pasta `CloseCare/backend`.
3. Copie `.env.example` para `.env`.
4. Edite `backend/.env` com os dados do seu ambiente:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=closecare
DB_USER=closecare_app
DB_PASSWORD=sua_senha_do_postgres
JWT_SECRET_KEY=coloque_uma_chave_aleatoria_com_pelo_menos_32_caracteres
JWT_EXPIRATION_MINUTES=30
COOKIE_SECURE=false
```

Use uma chave JWT aleatória e forte com pelo menos 32 caracteres. `COOKIE_SECURE=false` é apropriado apenas para desenvolvimento local via HTTP; em produção, configure HTTPS e ajuste essa opção. Não compartilhe nem versione o arquivo `.env` com credenciais reais.

### 4.2 Instalar dependências e inicializar as tabelas

No terminal, a partir da raiz `CloseCare/`:

```bash
python -m venv .venv
```

Ative o ambiente virtual:

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

Instale as dependências e inicialize o banco:

```bash
pip install -r backend/requirements.txt
cd backend
python init_db.py
```

O comando `init_db.py` testa a conexão com o PostgreSQL e cria as tabelas definidas nos modelos. Depois, inicie o servidor, ainda dentro de `backend/`:

```bash
uvicorn main:app --reload
```

A API ficará disponível em `http://localhost:8000`, e a documentação em `http://localhost:8000/docs`.

### Executar o frontend

Em outro terminal, a partir da raiz `CloseCare/`, execute:

```bash
python -m http.server 5500 --directory frontend
```

Abra `http://localhost:5500` no navegador. O frontend está configurado para chamar a API em `http://localhost:8000`. A origem `localhost:5500` é permitida pela configuração de CORS e pelas verificações de origem do backend.

Crie primeiro uma conta de profissional e entre para cadastrar horários. Em seguida, crie uma conta de paciente em outra sessão/navegador ou após sair da conta do profissional; o paciente poderá consultar os horários livres e realizar agendamentos.

## descrição dos testes realizados


## como ocorre a comunicação entre os componentes
