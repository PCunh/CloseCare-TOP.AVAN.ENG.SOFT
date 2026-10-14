from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import usuarios, auth, disponibilidade_esbc, agendamentos_esbc

app = FastAPI(title="CloseCare — ESBC", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
)
app.include_router(usuarios.router)
app.include_router(auth.router)
app.include_router(disponibilidade_esbc.router)
app.include_router(agendamentos_esbc.router)

@app.get("/health")
def health():
    return {"status": "ok", "projeto": "CloseCare ESBC"}
