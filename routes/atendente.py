from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
from database import get_session
from modelos.atendente import Atendente
from modelos.adocao import Adocao
from modelos.adocao_atend import AdocaoAtend


router = APIRouter(prefix="/atendentes", tags=["Atendentes"])


@router.post("/")
def create_atendente(atendente: Atendente, session: Session = Depends(get_session)):
    session.add(atendente)
    session.commit()
    session.refresh(atendente)
    return atendente

@router.get("/")
def listar_atendentes(
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    stmt = select(Atendente).offset(offset).limit(limit)
    return session.exec(stmt).all()
@router.put("/{atendente_id}")
def update_atendente(atendente_id: int, atendente: Atendente, session: Session = Depends(get_session)):
    db_atendente = session.get(Atendente, atendente_id)
    if not db_atendente:
        raise HTTPException(status_code=404, detail="Atendente não encontrado")

    for k, v in atendente.model_dump(exclude_unset=True).items():
        setattr(db_atendente, k, v)

    session.commit()
    session.refresh(db_atendente)
    return db_atendente

@router.delete("/{atendente_id}")
def delete_atendente(atendente_id: int, session: Session = Depends(get_session)):
    atendente = session.get(Atendente, atendente_id)
    if not atendente:
        raise HTTPException(status_code=404, detail="Atendente não encontrado")

    session.delete(atendente)
    session.commit()
    return {"ok": True}

# Buscar atendente por ID
@router.get("/{atendente_id}")
def get_atendente(atendente_id: int, session: Session = Depends(get_session)):
    atendente = session.get(Atendente, atendente_id)
    if not atendente:
        return {"erro": "Atendente não encontrado"}
    return atendente


# Buscar atendente pelo nome
@router.get("/buscar/nome")
def buscar_atendente_nome(
    nome: str,
    offset: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    stmt = (
        select(Atendente)
        .where(Atendente.nome.ilike(f"%{nome}%"))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()

 # Quantidade total de atendentes cadastrados
@router.get("/stats/total")
def total_atendentes(session: Session = Depends(get_session)):
    stmt = select(func.count(Atendente.id_atendente))
    return session.exec(stmt).one()

@router.get("/ordenar/nome")
def ordenar_atendentes_nome(
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    stmt = (
        select(Atendente)
        .order_by(Atendente.nome.asc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()
