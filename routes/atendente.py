from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from database import get_session
from modelos.atendente import Atendente, AtendenteBase
from modelos.adocao import AdocaoAtend

router = APIRouter(prefix="/atendentes", tags=["Atendentes"])

# Listar atendentes
@router.get("/")
def listar_atendentes(
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    stmt = select(Atendente).offset(offset).limit(limit)
    return session.exec(stmt).all()


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

@router.post("/")
def create_atendente(atendente: AtendenteBase, session: Session = Depends(get_session)):
    novo = Atendente(**atendente.model_dump())
    session.add(novo)
    session.commit()
    session.refresh(novo)
    return novo


@router.put("/{atendente_id}")
def update_atendente(atendente_id: int, atendente: AtendenteBase, session: Session = Depends(get_session)):
    db_atendente = session.get(Atendente, atendente_id)
    if not db_atendente:
        raise HTTPException(status_code=404, detail="Atendente não encontrado")

    dados = atendente.model_dump()
    dados.pop("id_atendente", None)

    for campo, valor in dados.items():
        setattr(db_atendente, campo, valor)

    session.commit()
    session.refresh(db_atendente)
    return db_atendente


@router.delete("/{atendente_id}")
def delete_atendente(atendente_id: int, session: Session = Depends(get_session)):
    atendente = session.get(Atendente, atendente_id)
    if not atendente:
        raise HTTPException(status_code=404, detail="Atendente não encontrado")

    existe = session.exec( 
        select(AdocaoAtend).where(AdocaoAtend.id_atendente == atendente_id)
    ).first()

    if existe:
        raise HTTPException(
            status_code=400,
            detail="Atendente possui atendimentos registrados e não pode ser removido"
        )

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