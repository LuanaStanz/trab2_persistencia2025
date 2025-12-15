from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import extract
from sqlalchemy.orm import selectinload
from database import get_session
from modelos.adocao import Adocao, AdocaoBase, AdocaoAtend
from modelos.animal import Animal
from modelos.adotante import Adotante

router = APIRouter(prefix="/adocoes", tags=["Adoções"])

# CREATE - nao deixa adotar se id do animal ou adotante nao existe. Nao deixa adotar animal adotado
@router.post("/")
def create_adocao(id_animal: int, id_adotante: int, adocao: AdocaoBase, session: Session = Depends(get_session)):
    animal = session.get(Animal, id_animal)
    if not animal:
        raise HTTPException(400, "Adocao não encontrado")
    
    if animal.status_adocao:
        raise HTTPException(
            status_code=409,
            detail="Animal já está adotado."
        )

    adotante = session.get(Adotante, id_adotante)
    if not adotante:
        raise HTTPException(status_code=400, detail="Adotante não encontrado")

    nova_adocao = Adocao(
        **adocao.model_dump(),
        id_animal=id_animal,
        id_adotante=id_adotante
    )

    session.add(nova_adocao)

    animal.status_adocao = True

    session.commit()
    session.refresh(nova_adocao)
    return nova_adocao

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
@router.get("/relatorio/completo/ordenados")
def relatorio_adocoes(offset: int = 0, limit: int = Query(default=10, le=100), session: Session = Depends(get_session)):
    p = (
        select(Adocao)
        .options(
            selectinload(Adocao.animal),
            selectinload(Adocao.adotante),
            selectinload(Adocao.atendentes).selectinload(AdocaoAtend.atendente),
        )
        .order_by(Adocao.data_adocao.desc())
        .offset(offset)
        .limit(limit)
    )
    adocoes = session.exec(p).all()

    if not adocoes:
        raise HTTPException(status_code=404, detail="Nenhuma adoção encontrada")
    
    return adocoes

# UPDATE
@router.put("/{adocao_id}")
def update_adocao(adocao_id: int, adocao: AdocaoBase, session: Session = Depends(get_session)):
    db_adocao = session.get(Adocao, adocao_id)
    if not db_adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    dados = adocao.model_dump(exclude_unset=True)

    # proteção extra (boa prática)
    dados.pop("id_adocao", None)

    for campo, valor in dados.items():
        setattr(db_adocao, campo, valor)

    session.commit()
    session.refresh(db_adocao)
    return db_adocao
    
# DELETE from history
@router.delete("/{adocao_id}/hard")
def complete_delete_adocao(adocao_id: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, adocao_id)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")
    
    for vinculo in adocao.atendentes:
        session.delete(vinculo)

    session.delete(adocao)
    session.commit()
    return {"ok": True, "deletada": True}

# DELETE (Soft Delete)
@router.delete("/{adocao_id}/cancelar")
def cancelar_adocao(adocao_id: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, adocao_id)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    if adocao.cancelamento:
        raise HTTPException(status_code=409,detail="Adoção já está cancelada")

    adocao.cancelamento = True

    animal = adocao.animal
    if animal:
        animal.status_adocao = False

    session.commit()
    return {"ok": True, "cancelada": True, "animal_liberado": True}

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
