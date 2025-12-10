```mermaid
erDiagram
    Animal {
        int id PK
        string nome
        string especie
        int idade
        date data_resgate
        string status_adocao
    }
    Atendimento {
        int id PK
        date data
        string descricao
        string medicamentos
        int animal_id FK
    }
    Adotante {
        int id PK
        string nome
        string contato
        string endereco
        string preferencias
    }
    Adocao {
        int animal_id PK, FK
        int adotante_id PK, FK
        date data_adocao
    }
    Animal ||--o{ Atendimento : "tem atendimentos"
    Animal }o--o{ Adocao : "relacionado por"
    Adotante }o--o{ Adocao : "adota via"

```
