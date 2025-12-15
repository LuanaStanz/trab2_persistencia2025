from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func, extract
from sqlalchemy.orm import selectinload, joinedload
from database import get_session
from modelos.adocao import Adocao
from modelos.animal import Animal
from modelos.adotante import Adotante
from modelos.atendente import Atendente

router = APIRouter(prefix="/adocoes", tags=["Adoções"])

# CREATE
@router.post("/")
def create_adocao(adocao: Adocao, session: Session = Depends(get_session)):
    session.add(adocao)
    session.commit()
    session.refresh(adocao)
    return adocao

# READ - Listar todos (com paginação + selectinload)
@router.get("/")
def listar_adocoes(
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    stmt = (
        select(Adocao)
        .options(
            selectinload(Adocao.animal),
            selectinload(Adocao.adotante),
            selectinload(Adocao.atendente),
        )
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()

# UPDATE
@router.put("/{adocao_id}")
def update_adocao(adocao_id: int, adocao: Adocao, session: Session = Depends(get_session)):
    db_adocao = session.get(Adocao, adocao_id)
    if not db_adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    for k, v in adocao.model_dump(exclude_unset=True).items():
        setattr(db_adocao, k, v)

    session.commit()
    session.refresh(db_adocao)
    return db_adocao

# DELETE
@router.delete("/{adocao_id}")
def cancelar_adocao(adocao_id: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, adocao_id)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    adocao.cancelamento = True
    session.commit()
    return {"ok": True, "cancelada": True}

# a/g) Consultas por ID - Buscar adoção por ID (com relacionamentos + selectinload)
@router.get("/{adocao_id}")
def get_adocao(adocao_id: int, session: Session = Depends(get_session)):
    stmt = (
        select(Adocao)
        .where(Adocao.id_adocao == adocao_id)
        .options(
            selectinload(Adocao.animal),
            selectinload(Adocao.adotante),
            selectinload(Adocao.atendente),
        )
    )
    return session.exec(stmt).first()

# Adoções por ano
@router.get("/ano")
def adocoes_por_ano(ano: int, session: Session = Depends(get_session)):
    stmt = select(Adocao).where(extract("year", Adocao.data_adocao) == ano)
    return session.exec(stmt).all()

# Adoções canceladas
@router.get("/canceladas")
def adocoes_canceladas(
    status: bool,
    offset: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    stmt = (
        select(Adocao)
        .where(Adocao.cancelamento == status)
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()


# Adoções mais recentes
@router.get("/recentes")
def adocoes_recentes(
    offset: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    stmt = (
        select(Adocao)
        .order_by(Adocao.data_adocao.desc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()


# Consulta complexa (JOIN explícito – relatório)
@router.get("/relatorio/completo")
def relatorio_adocoes(session: Session = Depends(get_session)):
)

# g) Consultas complexas envolvendo múltiplas entidades - Listar animais com `status_adocao = 1`, exibindo todas informações relacionadas a esse animal
