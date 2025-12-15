from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func, extract
from sqlalchemy.orm import selectinload
from database import get_session
from modelos.animal import Animal
from modelos.adocao import Adocao

router = APIRouter(prefix="/animais", tags=["Animais"])

# CREATE
@router.post("/")
def create_animal(animal: Animal, session: Session = Depends(get_session)):
    session.add(animal)
    session.commit()
    session.refresh(animal)
    return animal

# READ - Listar todos (com paginação)
@router.get("/")
def listar_animais(offset: int = 0, limit: int = Query(default=10, le=100), session: Session = Depends(get_session)):
    p = select(Animal).offset(offset).limit(limit)
    return session.exec(p).all()

# UPDATE
@router.put("/detalhes/{animal_id}")
def update_animal(animal_id: int, animal: Animal, session: Session = Depends(get_session)):
    db_animal = session.get(Animal, animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    for k, v in animal.model_dump(exclude_unset=True).items():
        setattr(db_animal, k, v)

    session.commit()
    session.refresh(db_animal)
    return db_animal

# DELETE
@router.delete("/{animal_id}")
def delete_animal(animal_id: int, session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    session.delete(animal)
    session.commit()
    return {"ok": True}

# a) Consultas por ID - Buscar Animal por ID
@router.get("/{animal_id}")
def animal_by_id(animal_id: int, session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        return {"erro": "Animal não encontrado"}
    return animal

# b) Listagens filtradas por relacionamentos - Listar todos os animais adotados por um adotante  
@router.get("/adotados/adotante")
def animal_by_adotante(adotante_id: int,offset: int = 0,limit: int = Query(default=10, le=100),session: Session = Depends(get_session)):
    p = (
        select(Animal)
        .join(Adocao, Adocao.id_animal == Animal.id_animal)
        .where(Adocao.id_adotante == adotante_id)
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# c) Buscas por texto parcial - Buscar animal pelo nome
@router.get("/buscar/nome")
def animal_by_name(nome: str, offset: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    p = (
        select(Animal)
        .where(Animal.nome.ilike(f"%{nome}%"))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# d) Filtros por data / ano - Animais resgatados em determinado ano  
@router.get("/ano/resgate")
def animais_por_ano(ano: int, session: Session = Depends(get_session)):
    p = select(Animal).where(extract("year", Animal.data_resgate) == ano)
    return session.exec(p).all()

# e) Contagens - Quantidade total de animais cadastrados  
@router.get("/stats/total")
def total_animais(session: Session = Depends(get_session)):
    return {"total de animais": session.exec(select(func.count(Animal.id_animal))).one()}
    
# e) Contagens - Quantidade de animais adotados por espécie  
@router.get("/stats/adotados/especie")
def adotados_por_especie(session: Session = Depends(get_session)):
    p = (
        select(Animal.especie, func.count())
        .where(Animal.status_adocao == 1)
        .group_by(Animal.especie)
    )
    return session.exec(p).all()

#  f) Classificações e ordenações - Listar animais com `status_adocao = 0`  ordenados por idade
@router.get("/disponiveis/ordenar/idade")
def animais_disponiveis(session: Session = Depends(get_session)):
    p = (
        select(Animal)
        .where(Animal.status_adocao == 0)
        .order_by(Animal.idade)
    )
    return session.exec(p).all()
