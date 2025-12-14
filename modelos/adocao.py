from datetime import date
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .animal import Animal
    from .adotante import Adotante
    from .adocao_atend import AdocaoAtend
    from .atendente import Atendente

class AdocaoBase(SQLModel):
    data_adocao: date
    descricao: str
    cancelamento: bool

class Adocao(AdocaoBase, table=True):
    id_adocao: int | None = Field(default=None, primary_key=True)
    id_animal: int = Field(foreign_key="animal.id_animal")
    id_adotante: int = Field(foreign_key="adotante.id_adotante")

    animal: "Animal" = Relationship(back_populates="adocoes")
    adotante: "Adotante" = Relationship(back_populates="adocoes")
    atendentes: list["AdocaoAtend"] = Relationship(back_populates="adocao")

#tabela de associação
class AdocaoAtend(SQLModel, table=True):
    id_adocao: int = Field(foreign_key="adocao.id_adocao", primary_key=True)
    id_atendente: int = Field(foreign_key="atendente.id_atendente", primary_key=True)

    adocao: "Adocao" = Relationship(back_populates="atendentes")
    atendente: "Atendente" = Relationship(back_populates="adocoes")
