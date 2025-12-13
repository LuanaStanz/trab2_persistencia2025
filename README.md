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
    InfoAdocao {
        int id PK
        date data
        string descricao
        string data_adocao
        int animal_id FK
    }
    Adotante {
        int id PK
        string nome
        string contato
        string endereco
        string preferencias
    }
    Ani_Adot {
        int animal_id PK, FK
        int adotante_id PK, FK
    }

    Animal ||--o{ InfoAdocao : "possui"
    Animal ||--o{ Ani_Adot : "envolvido em"
    Adotante ||--o{ Ani_Adot : "realiza"

```
