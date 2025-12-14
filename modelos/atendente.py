from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .adocao import AdocaoAtend

class AtendenteBase(SQLModel):
    nome: str

class Atendente(AtendenteBase, table=True):
    id_atendente: int | None = Field(default=None, primary_key=True)
    adocao_links: list["AdocaoAtend"] = Relationship(back_populates="atendente")