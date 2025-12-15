from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload
from database import get_session
from modelos.animal import Animal, AnimalBase, AniAdocaoAtendAdot
from modelos.adocao import Adocao, AdocaoAtend
from datetime import date


router = APIRouter(prefix="/animais", tags=["Animais"])

# CREATE
@router.post("/", response_model=Animal)
def create_animal(animal: AnimalBase, session: Session = Depends(get_session)):
    novo = Animal(**animal.model_dump())
    session.add(novo)
    session.commit()
    session.refresh(novo)
    return novo

# READ - Listar todos (com paginação)
@router.get("/", response_model=list[Animal])
def listar_animais(offset: int = 0,limit: int = Query(default=10, le=100),session: Session = Depends(get_session)):
    return session.exec(select(Animal).offset(offset).limit(limit)).all()

# b) Listagens filtradas por relacionamentos - Listar todos os animais adotados por um adotante  
@router.get("/adotados/adotante", response_model=list[Animal])
def animal_by_adotante(adotante_id: int,offset: int = 0,limit: int = Query(default=10, le=100), session: Session = Depends(get_session)):
    p = (
        select(Animal)
        .join(Adocao)
        .where(Adocao.id_adotante == adotante_id)
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# c) Buscas por texto parcial - Buscar animal pelo nome
@router.get("/buscar/nome", response_model=list[Animal])
def animal_by_name(
    nome: str,
    offset: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    p = (
        select(Animal)
        .where(Animal.nome.ilike(f"%{nome}%"))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# d) Filtros por data / ano - Animais resgatados em determinado ano 
@router.get("/resgatados/ano", response_model=list[Animal])
def animais_resgatados_por_ano(ano: int,offset: int = 0,limit: int = Query(default=10, le=100),session: Session = Depends(get_session)):
    p = (
        select(Animal)
        .where(Animal.data_resgate.between( date(ano, 1, 1), date(ano, 12, 31) ))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()

# e) Agregações e contagens - Quantidade total de animais cadastrados  
@router.get("/stats/total")
def total_animais(session: Session = Depends(get_session)):
    p = select(func.count(Animal.id_animal))
    return session.exec(p).one()

# e) Agregações e contagens - Quantidade total de animais cadastrados com `status_adocao = 0`  
@router.get("/stats/status/0")
def total_animais_disponiveis(session: Session = Depends(get_session)):
    p = (
        select(func.count(Animal.id_animal))
        .where(Animal.status_adocao == 0)
    )
    return session.exec(p).one()

# e) Agregações e contagens - Quantidade total de animais cadastrados com `status_adocao = 1`  
@router.get("/stats/status/1")
def total_animais_adotados(session: Session = Depends(get_session)):
    p = (
        select(func.count(Animal.id_animal))
        .where(Animal.status_adocao == 1)
    )
    return session.exec(p).one()

# f) Classificações e ordenações - Listar animais com `status_adocao = 0`  
@router.get("/disponiveis")
def listar_animais_disponiveis(
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    p = (
        select(Animal)
        .where(Animal.status_adocao == 0)
        .order_by(Animal.id_animal.asc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(p).all()


#  f) Classificações e ordenações - Listar animais ordenados por idade
@router.get("/ordenar/idade")
def ordenar_por_idade(status_adocao: int | None = None,offset: int = 0,limit: int = 10,session: Session = Depends(get_session)):
    p = select(Animal)
    if status_adocao is not None:
        p = p.where(Animal.status_adocao == status_adocao)
    p = p.order_by(Animal.idade.asc()).offset(offset).limit(limit)
    return session.exec(p).all()


# g) Consultas complexas envolvendo múltiplas entidades - 
# Listar animais exibindo todas suas informações relacionadas
@router.get("/detalhes", response_model=list[AniAdocaoAtendAdot])
def animais_adotados(
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    p = (
        select(Animal)
        .options(
            joinedload(Animal.adocoes).joinedload(Adocao.adotante),
            joinedload(Animal.adocoes).joinedload(Adocao.atendentes).joinedload(AdocaoAtend.atendente),
        )
        .offset(offset)
        .limit(limit)
    )

    animais = session.exec(p).unique().all()

    if not animais:
        raise HTTPException(status_code=404, detail="Nenhum animal encontrado")

    resposta = []

    for animal in animais:
        for adocao in animal.adocoes:
            resposta.append(
                AniAdocaoAtendAdot(
                    animal=animal,
                    adocao=adocao,
                    adotante=adocao.adotante,
                    atendentes=[link.atendente for link in adocao.atendentes]
                )
            )

    return resposta

# UPDATE
@router.put("/{animal_id}")
def update_animal(animal_id: int, animal: Animal, session: Session = Depends(get_session)):
    db_animal = session.get(Animal, animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    dados = animal.model_dump(exclude_unset=True)

    #garante que data_resgate seja date (SQLite exige)
    if "data_resgate" in dados and isinstance(dados["data_resgate"], str):
        dados["data_resgate"] = date.fromisoformat(dados["data_resgate"])

    # evita sobrescrever a PK
    dados.pop("id_animal", None)

    for campo, valor in dados.items():
        setattr(db_animal, campo, valor)

    session.commit()
    session.refresh(db_animal)
    return db_animal

#DELETE
@router.delete("/{animal_id}")
def delete_animal(animal_id: int, session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")

    if animal.adocoes:
        raise HTTPException(
            status_code=400,
            detail="Animal possui histórico de adoções e não pode ser removido"
        )

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

