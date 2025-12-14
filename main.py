from fastapi import FastAPI #uvicorn main:app --reload
from rotas import home, users, posts

# Inicializa o aplicativo FastAPI
app = FastAPI()

# Rotas para Endpoints
app.include_router(home.router)
app.include_router(animal.router)
app.include_router(adotante.router)
app.include_router(atendente.router)
app.include_router(adocao.router)