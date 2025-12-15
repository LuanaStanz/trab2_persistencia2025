from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import extract
from sqlalchemy.orm import selectinload, joinedload
from database import get_session
from modelos.adocao import Adocao
from modelos.animal import Animal

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
def listar_adocoes(offset: int = 0,limit: int = Query(default=10, le=100),session: Session = Depends(get_session)):
    return session.exec(select(Adocao).offset(offset).limit(limit)).all()

# Adoções canceladas
@router.get("/canceladas")
def adocoes_canceladas(status: bool,offset: int = 0,limit: int = 10,session: Session = Depends(get_session)):
    p = (
        select(Adocao)
        .where(Adocao.cancelamento == status)
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# Adoções mais recentes
@router.get("/recentes")
def adocoes_recentes(offset: int = 0,limit: int = 10,session: Session = Depends(get_session)):
    p = (
        select(Adocao)
        .order_by(Adocao.data_adocao.desc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# Consulta complexa (JOIN explícito – relatório)
@router.get("/relatorio/completo")
def relatorio_adocoes(session: Session = Depends(get_session)):
    p = (
        select(Adocao)
        .options(
            joinedload(Adocao.animal),
            joinedload(Adocao.adotante),
            joinedload(Adocao.atendentes).joinedload(AdocaoAtend.atendente),
        )
    )
    adocoes = session.exec(p).all()
    if not adocoes:
        raise HTTPException(status_code=404, detail="Nenhuma adoção encontrada")
    return adocoes

# g) Consultas complexas envolvendo múltiplas entidades - 
# Listar animais com `status_adocao = 1`, exibindo todas informações relacionadas a esse animal
@router.get("/detalhes")
def animais_adotados(session: Session = Depends(get_session)):
    p = (
        select(Animal)
        .where(Animal.status_adocao == 1)
        .options(
            selectinload(Animal.adocoes).selectinload(Adocao.adotante),
            selectinload(Animal.adocoes).selectinload(Adocao.atendentes).selectinload(AdocaoAtend.atendente),
        )
    )
    animais = session.exec(p).all()
    if not animais:
        raise HTTPException(status_code=404, detail="Nenhum animal adotado encontrado")
    return animais

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
    
# DELETE from history
@router.delete("/{adocao_id}/hard")
def complete_delete_adocao(adocao_id: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, adocao_id)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    session.delete(adocao)
    session.commit()
    return {"ok": True, "deletada": True}

# DELETE (Soft Delete)
@router.delete("/{adocao_id}/cancelar")
def cancelar_adocao(adocao_id: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, adocao_id)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    adocao.cancelamento = True
    session.commit()
    return {"ok": True, "cancelada": True}

# Adoções por ano
@router.get("/ano/{ano}")
def adocoes_por_ano(ano: int, session: Session = Depends(get_session)):
    p = select(Adocao).where(extract("year", Adocao.data_adocao) == ano)
    return session.exec(p).all()

# a/g) Consultas por ID - Buscar adoção por ID (com relacionamentos + selectinload)
@router.get("/id/{adocao_id}")
def get_adocao(adocao_id: int, session: Session = Depends(get_session)):
    p = (
        select(Adocao)
        .where(Adocao.id_adocao == adocao_id)
        .options(
            selectinload(Adocao.animal),
            selectinload(Adocao.adotante),
            selectinload(Adocao.atendentes).selectinload(AdocaoAtend.atendente),
        )
    )
    adocao = session.exec(p).first()
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")
    return adocao
