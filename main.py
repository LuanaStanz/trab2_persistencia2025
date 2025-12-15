from fastapi import FastAPI #uvicorn main:app --reload
from contextlib import asynccontextmanager
from database import engine
from routes import animal,adotante,atendente,adocao

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Sistema de Adoção de Animais",
    lifespan=lifespan
)

# Incluindo as rotas
app.include_router(animal.router)
app.include_router(adotante.router)
app.include_router(atendente.router)
app.include_router(adocao.router)

@app.get("/")
def root():
    return {"message": "API de Adoção funcionando!"}