from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List
from datetime import date
from database import get_session
from modelos.animal import Animal, AnimalBase

router = APIRouter(prefix="/animais", tags=["Animais"])

# --- CREATE (Criar Animal) ---
@router.post("/", response_model=Animal, status_code=201)
def criar_animal(animal: AnimalBase, session: Session = Depends(get_session)):
    db_animal = Animal.model_validate(animal)
    session.add(db_animal)
    try:
        session.commit()
        session.refresh(db_animal)
        return db_animal
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar animal: {e}")

# --- READ (Listar com Filtros e Ordenação) ---
@router.get("/", response_model=List[Animal])
def listar_animais(
    session: Session = Depends(get_session),
    nome: str | None = Query(None, description="Filtro: Nome parcial"),
    ano_resgate: int | None = Query(None, description="Filtro: Ano de resgate"),
    status_adocao: bool | None = Query(None, description="Filtro: Status (True=Adotado, False=Disponível)"),
    ordenar_por_idade: bool = Query(False, description="Ordenar do mais novo ao mais velho")
):
    query = select(Animal)

    if nome:
        query = query.where(func.lower(Animal.nome).contains(nome.lower()))
    
    if ano_resgate:
        start_date = date(ano_resgate, 1, 1)
        end_date = date(ano_resgate, 12, 31)
        query = query.where(Animal.data_resgate >= start_date, Animal.data_resgate <= end_date)

    if status_adocao is not None:
        query = query.where(Animal.status_adocao == status_adocao)

    if ordenar_por_idade:
        query = query.order_by(Animal.idade)

    return session.exec(query).all()

# --- READ (Buscar por ID) ---
@router.get("/{animal_id}", response_model=Animal)
def obter_animal(animal_id: int, session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return animal

# --- UPDATE  ---
@router.patch("/{animal_id}", response_model=Animal)
def atualizar_animal(animal_id: int, animal_data: AnimalBase, session: Session = Depends(get_session)):
    db_animal = session.get(Animal, animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    
    dados = animal_data.model_dump(exclude_unset=True)
    for key, value in dados.items():
        setattr(db_animal, key, value)

    session.add(db_animal)
    session.commit()
    session.refresh(db_animal)
    return db_animal

# --- DELETE  ---
@router.delete("/{animal_id}")
def deletar_animal(animal_id: int, session: Session = Depends(get_session)):
    db_animal = session.get(Animal, animal_id)
    if not db_animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    
    session.delete(db_animal)
    session.commit()
    return {"message": "Animal removido com sucesso"}

@router.get("/stats/contagem")
def estatisticas_animais(session: Session = Depends(get_session)):
    total = session.exec(select(func.count(Animal.id_animal))).one()
    disponiveis = session.exec(select(func.count(Animal.id_animal)).where(Animal.status_adocao == False)).one()
    adotados = session.exec(select(func.count(Animal.id_animal)).where(Animal.status_adocao == True)).one()
    
    return {
        "total_animais": total,
        "disponiveis": disponiveis,
        "adotados": adotados
    }
    
@router.get("/ordenados/idade", response_model=List[Animal])
def listar_animais_por_idade(
    session: Session = Depends(get_session)
):
    # Do mais novo (menor idade) para o mais velho (maior idade)
    query = select(Animal).order_by(Animal.idade.asc())
    return session.exec(query).all()

