from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from datetime import date
from database import get_session

from modelos.adocao import Adocao, AdocaoBase, AdocaoAtend
from modelos.animal import Animal
from modelos.adotante import Adotante
from modelos.atendente import Atendente

router = APIRouter(prefix="/adocoes", tags=["Adoções"])

# Modelo auxiliar para criação (DTO)
class AdocaoCreate(AdocaoBase):
    id_animal: int
    id_adotante: int
    ids_atendentes: List[int] 

# --- CREATE (Processar Adoção) ---
@router.post("/", response_model=Adocao, status_code=201)
def realizar_adocao(adocao_in: AdocaoCreate, session: Session = Depends(get_session)):
    # 1. Validações
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
        # 2. Criação da Adoção
        dados_adocao = adocao_in.model_dump(exclude={"ids_atendentes"})
        nova_adocao = Adocao.model_validate(dados_adocao)
        
        session.add(nova_adocao)
        session.flush()

        # 3. Relacionamento N:M
        for id_atend in adocao_in.ids_atendentes:
            link = AdocaoAtend(id_adocao=nova_adocao.id_adocao, id_atendente=id_atend)
            session.add(link)

        # 4. Atualizar Status do Animal
        animal.status_adocao = True
        session.add(animal)

        session.commit()
        session.refresh(nova_adocao)
        return nova_adocao

    except Exception as e:
        session.rollback() 
        raise HTTPException(status_code=500, detail=f"Erro ao processar adoção: {e}")

# --- READ (Listagem com TODOS os Filtros) ---
@router.get("/", response_model=List[Adocao])
def listar_adocoes(
    session: Session = Depends(get_session),
    id_animal: int | None = Query(None, description="Filtrar por ID do Animal"),
    id_adotante: int | None = Query(None, description="Filtrar por ID do Adotante"),
    id_atendente: int | None = Query(None, description="Filtrar por ID do Atendente"),
    especie: str | None = Query(None, description="Filtrar por espécie (ex: Gato, Cachorro)"),
    cancelamento: bool | None = Query(None, description="Filtrar por status de cancelamento"),
    ano: int | None = Query(None, description="Filtrar por ano da adoção (ex: 2025)"),
    ordenar_recentes: bool = Query(False, description="Se True, ordena da mais recente para a mais antiga")
):
    query = select(Adocao)

    if id_animal:
        query = query.where(Adocao.id_animal == id_animal)
    if id_adotante:
        query = query.where(Adocao.id_adotante == id_adotante)
    if id_atendente:
        query = query.join(AdocaoAtend).where(AdocaoAtend.id_atendente == id_atendente)
    if especie:
        query = query.join(Animal).where(Animal.especie == especie)
    if cancelamento is not None:
        query = query.where(Adocao.cancelamento == cancelamento)
    if ano:
        start_date = date(ano, 1, 1)
        end_date = date(ano, 12, 31)
        query = query.where(Adocao.data_adocao >= start_date, Adocao.data_adocao <= end_date)
    if ordenar_recentes:
        query = query.order_by(Adocao.data_adocao.desc())

    return session.exec(query).all()

# --- READ (Por ID) ---
@router.get("/{id_adocao}", response_model=Adocao)
def buscar_adocao_por_id(id_adocao: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, id_adocao)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")
    return adocao

# --- UPDATE (Atualizar Adoção) ---
@router.put("/{id_adocao}", response_model=Adocao)
def atualizar_adocao(id_adocao: int, adocao_in: AdocaoCreate, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, id_adocao)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    # Validações de existência
    if not session.get(Animal, adocao_in.id_animal):
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    if not session.get(Adotante, adocao_in.id_adotante):
        raise HTTPException(status_code=404, detail="Adotante não encontrado")
    for id_atend in adocao_in.ids_atendentes:
        if not session.get(Atendente, id_atend):
            raise HTTPException(status_code=404, detail=f"Atendente {id_atend} não encontrado")

    try:
        # Atualiza campos básicos
        dados = adocao_in.model_dump(exclude={"ids_atendentes"})
        for campo, valor in dados.items():
            setattr(adocao, campo, valor)

        # Atualiza Atendentes (Remove antigos e adiciona novos)
        for link in adocao.atendentes:
            session.delete(link)
        
        for id_atend in adocao_in.ids_atendentes:
            session.add(AdocaoAtend(id_adocao=id_adocao, id_atendente=id_atend))

        session.add(adocao)
        session.commit()
        session.refresh(adocao)
        return adocao

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar adoção: {e}")

# --- DELETE (Deletar Adoção) ---
@router.delete("/{id_adocao}", status_code=204)
def deletar_adocao(id_adocao: int, session: Session = Depends(get_session)):
    adocao = session.get(Adocao, id_adocao)
    if not adocao:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    try:
        # Se deletar a adoção, o animal volta a ficar disponível!
        animal = session.get(Animal, adocao.id_animal)
        if animal:
            animal.status_adocao = False
            session.add(animal)

        # Remove vínculos da tabela associativa
        for link in adocao.atendentes:
            session.delete(link)

        session.delete(adocao)
        session.commit()

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar adoção: {e}")

# --- RELATÓRIOS ---
@router.get("/relatorio/detalhes") 
def listar_adocoes_detalhadas(session: Session = Depends(get_session)):
    query = select(Adocao, Animal, Adotante).join(Animal).join(Adotante)
    resultados = session.exec(query).all()
    lista_detalhada = []
    for adocao, animal, adotante in resultados:
        atendentes_nomes = [link.atendente.nome for link in adocao.atendentes if link.atendente]
        lista_detalhada.append({
            "id_adocao": adocao.id_adocao,
            "data": adocao.data_adocao,
            "animal": {"nome": animal.nome},
            "adotante": {"nome": adotante.nome},
            "atendentes": atendentes_nomes
        })
    return lista_detalhada

@router.get("/relatorio/animais-adotados")
def relatorio_animais_adotados(session: Session = Depends(get_session)):
    """Requisito G: Animais adotados com dados completos"""
    query = select(Adocao, Animal, Adotante).where(Adocao.id_animal == Animal.id_animal).where(Adocao.id_adotante == Adotante.id_adotante)
    resultados = session.exec(query).all()
    relatorio = []
    for adocao, animal, adotante in resultados:
        if not animal.status_adocao: continue
        
        lista_atendentes = []
        for link in adocao.atendentes:
            if link.atendente:
                lista_atendentes.append({"id": link.atendente.id_atendente, "nome": link.atendente.nome})

        relatorio.append({
            "animal": {"id": animal.id_animal, "nome": animal.nome, "especie": animal.especie},
            "adotante": {"id": adotante.id_adotante, "nome": adotante.nome},
            "dados_adocao": {"data": adocao.data_adocao, "atendentes": lista_atendentes}
        })
    return relatorio
