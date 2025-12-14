import random
from sqlmodel import Session, select
from faker import Faker
from database import engine

from modelos.animal import Animal
from modelos.adotante import Adotante
from modelos.atendente import Atendente
from modelos.adocao import Adocao, AdocaoAtend

fake = Faker('pt_BR')

def povoar_banco():
    with Session(engine) as session:
        print("--- Iniciando Povoamento Automático ---")

        print("Criando 10 Atendentes...")
        atendentes = []
        for _ in range(10):
            atend = Atendente(nome=fake.name())
            session.add(atend)
            atendentes.append(atend)
        session.commit()
        for a in atendentes: session.refresh(a)

        print("Criando 10 Adotantes...")
        adotantes = []
        for _ in range(10):
            adot = Adotante(
                nome=fake.name(),
                contato=fake.phone_number(),
                endereco=fake.address(),
                preferencias=random.choice(["Cães", "Gatos", "Pequeno porte", "Indiferente"])
            )
            session.add(adot)
            adotantes.append(adot)
        session.commit()
        for a in adotantes: session.refresh(a)

        print("Criando 20 Animais...")
        animais = []
        especies = ["Cachorro", "Gato", "Coelho", "Papagaio"]
        for _ in range(20):
            ja_adotado = random.choice([True, False]) # Sorteia se já foi adotado
            
            animal = Animal(
                nome=fake.first_name(),
                especie=random.choice(especies),
                idade=random.randint(1, 15),
                data_resgate=fake.date_between(start_date='-5y', end_date='today'),
                status_adocao=ja_adotado
            )
            session.add(animal)
            animais.append(animal)
        session.commit()
        for a in animais: session.refresh(a)

        print("Gerando Adoções...")
        for animal in animais:
            if animal.status_adocao:
                adotante_sorteado = random.choice(adotantes)
                
                nova_adocao = Adocao(
                    data_adocao=fake.date_between(start_date=animal.data_resgate, end_date='today'),
                    descricao=fake.sentence(),
                    cancelamento=False,
                    id_animal=animal.id_animal,
                    id_adotante=adotante_sorteado.id_adotante
                )
                session.add(nova_adocao)
                session.flush() 
                
                atend_sorteado = random.choice(atendentes)
                link = AdocaoAtend(
                    id_adocao=nova_adocao.id_adocao,
                    id_atendente=atend_sorteado.id_atendente
                )
                session.add(link)

        session.commit()
        print("--- Banco Povoado com Sucesso! ---")

if __name__ == "__main__":
    povoar_banco()