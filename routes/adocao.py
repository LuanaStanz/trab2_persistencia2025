from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from database import get_session

from modelos.adocao import Adocao, AdocaoBase, AdocaoAtend
from modelos.animal import Animal
from modelos.adotante import Adotante
from modelos.atendente import Atendente

router = APIRouter(prefix="/adocoes", tags=["Adoções"])

class AdocaoCreate(AdocaoBase):
    id_animal: int
    id_adotante: int
    ids_atendentes: List[int] 

@router.post("/", response_model=Adocao, status_code=201)
def realizar_adocao(adocao_in: AdocaoCreate, session: Session = Depends(get_session)):
    animal = session.get(Animal, adocao_in.id_animal)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    if animal.status_adocao: 
        raise HTTPException(status_code=400, detail="Este animal já foi adotado!")

    adotante = session.get(Adotante, adocao_in.id_adotante)
    if not adotante:
        raise HTTPException(status_code=404, detail="Adotante não encontrado")

    for id_atend in adocao_in.ids_atendentes:
        if not session.get(Atendente, id_atend):
            raise HTTPException(status_code=404, detail=f"Atendente {id_atend} não encontrado")

    try:
       
        dados_adocao = adocao_in.model_dump(exclude={"ids_atendentes"})
        nova_adocao = Adocao.model_validate(dados_adocao)
        
        session.add(nova_adocao)
        session.flush()

        for id_atend in adocao_in.ids_atendentes:
            link = AdocaoAtend(id_adocao=nova_adocao.id_adocao, id_atendente=id_atend)
            session.add(link)

        animal.status_adocao = True
        session.add(animal)

        session.commit()
        session.refresh(nova_adocao)
        return nova_adocao

    except Exception as e:
        session.rollback() 
        raise HTTPException(status_code=500, detail=f"Erro ao processar adoção: {e}")

# --- READ (Listagem com Filtros de Relacionamento) ---
@router.get("/", response_model=List[Adocao])
def listar_adocoes(
    session: Session = Depends(get_session),
    id_animal: int | None = Query(None, description="Listar adoções deste Animal"),
    id_adotante: int | None = Query(None, description="Listar adoções deste Adotante"),
    id_atendente: int | None = Query(None, description="Listar adoções deste Atendente"),
):
    query = select(Adocao)

    # Filtro por Animal
    if id_animal:
        query = query.where(Adocao.id_animal == id_animal)
    
    # Filtro por Adotante
    if id_adotante:
        query = query.where(Adocao.id_adotante == id_adotante)

    # Filtro por Atendente
    if id_atendente:
        query = query.join(AdocaoAtend).where(AdocaoAtend.id_atendente == id_atendente)

    return session.exec(query).all()

@router.get("/detalhes")
def listar_adocoes_detalhadas(session: Session = Depends(get_session)):
    """
    Lista adoções com dados completos: Animal, Adotante e Atendentes.
    """
    #Join entre as tabelas
    query = select(Adocao, Animal, Adotante).join(Animal).join(Adotante)
    resultados = session.exec(query).all()

    lista_detalhada = []
    for adocao, animal, adotante in resultados:
        atendentes_nomes = [link.atendente.nome for link in adocao.atendentes if link.atendente]
        
        lista_detalhada.append({
            "id_adocao": adocao.id_adocao,
            "data": adocao.data_adocao,
            "animal": {
                "id": animal.id_animal,
                "nome": animal.nome,
                "especie": animal.especie
            },
            "adotante": {
                "id": adotante.id_adotante,
                "nome": adotante.nome
            },
            "atendentes": atendentes_nomes
        })
    
    return lista_detalhada