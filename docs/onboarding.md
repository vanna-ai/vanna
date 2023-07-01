## What do I need to do to use **Vanna.AI**?
Vanna.AI uses a combination of documentation and historical question and SQL pairs to generate SQL from natural language.

### Step 1: Train **Vanna.AI**
- Give **Vanna.AI** sample SQL
- **Vanna.AI** will try to guess the question
- Verify the question is correct
```mermaid
flowchart LR
    Generate[vn.generate_question]
    Question[Question]
    Verify{Is the question correct?}
    SQL --> Generate
    Generate --> Question
    Question --> Verify
    Verify -- Yes --> Store[vn.store_sql]
    Verify -- No --> Update[Update the Question]
    Update --> Store
    
```

### Step 2: Ask **Vanna.AI** a Question
```mermaid
flowchart LR
    Question[Question]
    Generate[vn.generate_sql]
    SQL[SQL]
    Question --> Generate
    Generate --> SQL    
```
