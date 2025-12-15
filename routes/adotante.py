from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from database import get_session
from modelos.adotante import Adotante

router = APIRouter(prefix="/adotantes", tags=["Adotantes"])

# CREATE
@router.post("/")
def create_adotante(adotante: Adotante, session: Session = Depends(get_session)):
    print("Creating adotante:", adotante)
    session.add(adotante)
    session.commit()
    session.refresh(adotante)
    return adotante

# READ - Listar todos adotantes (paginação)
@router.get("/")
def read_adotantes(offset: int = 0,limit: int = Query(default=10, le=100),session: Session = Depends(get_session)):
    stmt = select(Adotante).offset(offset).limit(limit)
    return session.exec(stmt).all()

#  c) Buscas por texto parcial - Buscar adotante pelo nome
@router.get("/buscar/nome")
def by_name_adotante(nome: str,offset: int = 0,limit: int = 10,session: Session = Depends(get_session)):
    stmt = (
        select(Adotante)
        .where(Adotante.nome.ilike(f"%{nome}%"))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()

# a) Consultas por ID - Buscar adotante por ID
@router.get("/{adotante_id}")
def read_adotante(adotante_id: int, session: Session = Depends(get_session)):
    adotante = session.get(Adotante, adotante_id)
    if not adotante:
        return {"erro": "Adotante não encontrado"}
    return adotante

# UPDATE
@router.put("/{adotante_id}")
def update_adotante(adotante_id: int, adotante: Adotante, session: Session = Depends(get_session)):
    db_adotante = session.get(Adotante, adotante_id)
    if not db_adotante:
        raise HTTPException(status_code=404, detail="Adotante não encontrado")

    for k, v in adotante.model_dump(exclude_unset=True).items():
        setattr(db_adotante, k, v)

    session.commit()
    session.refresh(db_adotante)
    return db_adotante

# DELETE
@router.delete("/{adotante_id}")
def delete_adotante(adotante_id: int, session: Session = Depends(get_session)):
    adotante = session.get(Adotante, adotante_id)
    if not adotante:
        raise HTTPException(status_code=404, detail="Adotante não encontrado")

    session.delete(adotante)
    session.commit()
    return {"ok": True}

