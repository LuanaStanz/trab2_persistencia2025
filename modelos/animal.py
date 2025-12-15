from datetime import date
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from .adocao import AdocaoBase
from .adotante import AdotanteBase
from .atendente import AtendenteBase

if TYPE_CHECKING:
    from .adocao import Adocao

class AnimalBase(SQLModel):
    nome: str 
    especie: str 
    idade: int 
    data_resgate: date
    status_adocao: bool = False

class Animal(AnimalBase, table=True):
    id_animal: int | None = Field(default=None, primary_key=True)
    adocoes: list["Adocao"] = Relationship(back_populates="animal")

class AniAdocaoAtendAdot(SQLModel):
    animal: AnimalBase
    adocao: AdocaoBase | None
    adotante: AdotanteBase | None
    atendentes: list[AtendenteBase] | None