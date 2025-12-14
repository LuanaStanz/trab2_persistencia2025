from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .adocao import Adocao

class AdotanteBase(SQLModel):
    nome: str
    contato: str
    endereco: str
    preferencias: str  # preferência de espécie

class Adotante(AdotanteBase, table=True):
    id_adotante: int | None = Field(default=None, primary_key=True) #boas práticas
    adocoes: list["Adocao"] = Relationship(back_populates="adotante")
