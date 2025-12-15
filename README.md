Este projeto implementa uma API REST para gerenciamento de um sistema de adoção de animais, utilizando FastAPI, SQLModel, Alembic e SQLite/PostgreSQL (local e na nuvem usando o supabase).

# Diagrama de Classe:
```mermaid
classDiagram
    direction LR
    class Animal {
        id_animal: int
        nome: str
        especie: str
        idade: int
        data_resgate: date
        status_adocao: str
    }

    class Adotante {
        id_adotante: int
        nome: str
        contato: str
        endereco: str
        preferencias: str
    }

    class Adocao {
        id_adocao: int
        data_adocao: date
        descricao: str
        cancelamento: bool
    }

    class Atendente {
        id_atendente: int
        nome: str
    }

    Animal "1" -- "*" Adocao 
    Adotante "1" -- "*" Adocao
    Adocao "*" -- "*" Atendente 
```

# Diagrama ER:
```mermaid
erDiagram
    Animal {
        int id_animal PK
        string nome
        string especie
        int idade
        date data_resgate
        string status_adocao
    }

    Adotante {
        int id_adotante PK
        string nome
        string contato
        string endereco
        string preferencias
    }

    Adocao {
        int id_adocao PK
        int id_animal  FK
        int id_adotante FK
        date data_adocao
        string descricao
        bool cancelamento
    }
    AdocaoAtend{
        int id_adocao PK, FK
        int id_atendente PK, FK
    }
    
    Atendente {
        int id_atendente PK
        str nome
    }

    Animal ||--o{ Adocao : "tem"
    Adotante ||--o{ Adocao : "tem"
    Adocao ||--o{ AdocaoAtend : "tem"
    Atendente ||--o{ AdocaoAtend : "tem"
```
PS: A tabela AdocaoAtend é uma tabela associativa, necessária para representar o relacionamento muitos-para-muitos entre Adocao e Atendente.

## Animais

| Método | Endpoint | Descrição |
|------|---------|-----------|
| POST | `/animais/` | Criar animal |
| GET | `/animais/` | Listar animais |
| GET | `/animais/adotados/adotante` | Animais adotados por adotante |
| GET | `/animais/buscar/nome` | Buscar animal por nome |
| GET | `/animais/resgatados/ano` | Animais resgatados por ano |
| GET | `/animais/stats/total` | Total de animais |
| GET | `/animais/stats/status/0` | Total de animais disponíveis |
| GET | `/animais/stats/status/1` | Total de animais adotados |
| GET | `/animais/disponiveis` | Listar animais disponíveis |
| GET | `/animais/ordenar/idade` | Ordenar animais por idade |
| GET | `/animais/detalhes` | Animais adotados (com detalhes) |
| PUT | `/animais/{animal_id}` | Atualizar animal |
| DELETE | `/animais/{animal_id}` | Deletar animal |
| GET | `/animais/{animal_id}` | Buscar animal por ID |

---

## Adotantes

| Método | Endpoint | Descrição |
|------|---------|-----------|
| POST | `/adotantes/` | Criar adotante |
| GET | `/adotantes/` | Listar adotantes |
| GET | `/adotantes/buscar/nome` | Buscar adotante por nome |
| GET | `/adotantes/{adotante_id}` | Buscar adotante por ID |
| PUT | `/adotantes/{adotante_id}` | Atualizar adotante |
| DELETE | `/adotantes/{adotante_id}` | Deletar adotante |

---

## Atendentes

| Método | Endpoint | Descrição |
|------|---------|-----------|
| GET | `/atendentes/` | Listar atendentes |
| POST | `/atendentes/` | Criar atendente |
| GET | `/atendentes/buscar/nome` | Buscar atendente por nome |
| PUT | `/atendentes/{atendente_id}` | Atualizar atendente |
| DELETE | `/atendentes/{atendente_id}` | Deletar atendente |
| GET | `/atendentes/{atendente_id}` | Buscar atendente por ID |

---

## Adoções

| Método | Endpoint | Descrição |
|------|---------|-----------|
| POST | `/adocoes/` | Criar adoção |
| GET | `/adocoes/` | Listar adoções |
| GET | `/adocoes/canceladas` | Adoções canceladas |
| GET | `/adocoes/recentes` | Adoções mais recentes |
| GET | `/adocoes/relatorio/completo/ordenados` | Relatório completo de adoções |
| PUT | `/adocoes/{adocao_id}` | Atualizar adoção |
| DELETE | `/adocoes/{adocao_id}/hard` | Deletar adoção (hard delete) |
| DELETE | `/adocoes/{adocao_id}/cancelar` | Cancelar adoção (soft delete) |
| GET | `/adocoes/ano/{ano}` | Adoções por ano |
| GET | `/adocoes/id/{adocao_id}` | Buscar adoção por ID |

---
ps: as consultas foram implementadas diretamente nas rotas da API, organizadas por entidade, utilizando SQLModel e SQLAlchemy para realizar as operações necessárias de filtragem.
  
# Estrutura/Pastas do código: 
```txt
trab2_persistencia_2025/
├── README.md                    #descrição do projeto
├── .venv/                       #ambiente virtual criado pelo uv
├── pyproject.toml               #metadados e dependências do projeto (uv)
├── uv.lock                      #lockfile com versões exatas das dependências
├── .python-version              #versão do Python usado no projeto
|
├── alembic.ini                  #configuração principal do Alembic (onde estão as migrações, como conectar ao banco). Lê a URL do .env
├── .env                         #variáveis de ambiente (URLs de banco SQLite e PostgreSQL, etc.)
|
├── main.py                      #cria app FastAPI, inclui as rotas, arq usado pelo unicorn
├── database.py                  #centraliza: URL do banco, cria engine do SQLAlchemy, sessão (usado por todas as rotas)
│
├── modelos/                     #Define o esquema do banco (SQLModel). Cada arq é uma tabela. Alembic usa para gerar migrações
│   ├── __init__.py              # organiza
│   ├── animal.py                # Modelo da entidade Animal
│   ├── adotante.py              # Modelo da entidade Adotante
│   ├── atendente.py             # Modelo da entidade Atendente
│   ├── adocao.py                # Modelo da entidade Adocao
│   └── adocao_atend.py          # Tabela associativa (Adocao <-> Atendente)
│
├── rotas/                       #define endpoints HTTP da API (FastAPI routers). Usa os modelos e contem CRUD, consultas complexas e filtros
│   ├── animal.py                # Rotas CRUD e consultas de Animal
│   ├── adotante.py              # Rotas CRUD e consultas de Adotante
│   ├── atendente.py             # Rotas CRUD e consultas de Atendente
│   └── adocao.py                # Rotas CRUD e consultas complexas de Adocao
│
├── migrations/                  #controle de migrações/versionamento do banco. Alembic cria e executa SQL. Garante: reprodutibilidade e  histórico de mudanças
│   ├── versions/                # Arquivos de versão das migrações
│   │   ├── 4cf525d5891f_init_tables.py     # Migração inicial (criação das tabelas)
│   ├── env.py                   # conecta Alembic ao SQLModel
│   ├── README.md                # Explicação básica do Alembic
│   └── script.py.mako           # template das migrações
```
PS: A tabela AdocaoAtend é uma tabela associativa, necessária para representar o relacionamento muitos-para-muitos entre Adocao e Atendente.

## Relacionamentos implementados
1:N
Animal → Adoção
Adotante → Adoção
N:M
Adoção ↔ Atendente (via tabela associativa)

## Como Executar
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
uv sync

# Executar a aplicação
uvicorn main:app --reload
```

### Divisão de trabalho da Equipe
Jade - ideia de sistema, modelagem de classe e er, teste da api

Luana - migration, conexão com o 3 banco de dados, endpoints, teste da api

Maria Beatriz - api, endpoints, povoamento inicial, teste da api
