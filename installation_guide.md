# Guia de Instalação - Sistema de Editais UniRV

## 📂 Estrutura Final dos Arquivos

```
editais_unirv/
│
├── config/
│   ├── __init__.py                  # Arquivo vazio
│   └── config.py                    # COPIAR do artifact "project_structure"
│
├── core/
│   ├── __init__.py                  # Arquivo vazio
│   ├── scraper.py                   # COPIAR do artifact "project_structure"
│   ├── pdf_extractor.py             # COPIAR do artifact "fapeg_pdf_extractor"
│   └── nlp_analyzer.py              # COPIAR do artifact "nlp_extractor"
│
├── utils/
│   ├── __init__.py                  # Arquivo vazio
│   ├── cache.py                     # COPIAR do artifact "project_structure"
│   └── structure_monitor.py         # COPIAR do artifact "project_structure"
│
├── database/
│   ├── __init__.py                  # Arquivo vazio
│   └── db_manager.py                # COPIAR do artifact "database_schema"
│
├── main.py                          # COPIAR do artifact "project_structure"
├── requirements.txt                 # COPIAR do artifact "project_structure"
└── README.md                        # Criar com informações do projeto
```

## 🔧 Instalação Passo a Passo

### Passo 1: Criar Estrutura de Pastas

```bash
# No terminal/prompt
mkdir editais_unirv
cd editais_unirv

# Criar subpastas
mkdir config core utils database

# Criar arquivos __init__.py (necessários para Python)
touch config/__init__.py
touch core/__init__.py
touch utils/__init__.py
touch database/__init__.py

# No Windows use:
# type nul > config\__init__.py
# type nul > core\__init__.py
# etc...
```

### Passo 2: Copiar Código dos Artifacts

**IMPORTANTE**: Pegue o código de cada artifact que enviei e coloque nos arquivos correspondentes:

#### config/config.py
```python
# Copie APENAS a seção "ARQUIVO: config/config.py"
# do artifact "project_structure"
```

#### core/scraper.py
```python
# Copie APENAS a seção "ARQUIVO: core/scraper.py"
# do artifact "project_structure"
```

#### core/pdf_extractor.py
```python
# Copie TODO o código do artifact "fapeg_pdf_extractor"
# (aquele que tem a classe EditalPDFExtractor)
```

#### core/nlp_analyzer.py
```python
# Copie TODO o código do artifact "nlp_extractor"
# (aquele que tem a classe EditalNLPAnalyzer)
```

#### utils/cache.py
```python
# Copie APENAS a seção "ARQUIVO: utils/cache.py"
# do artifact "project_structure"
```

#### utils/structure_monitor.py
```python
# Copie APENAS a seção "ARQUIVO: utils/structure_monitor.py"
# do artifact "project_structure"
```

#### database/db_manager.py
```python
# Copie TODO o código do artifact "database_schema"
# (aquele que tem a classe EditalDatabase)
```

#### main.py
```python
# Copie APENAS a seção "ARQUIVO: main.py"
# do artifact "project_structure"
```

#### requirements.txt
```
# Copie o conteúdo da seção "ARQUIVO: requirements.txt"
# do artifact "project_structure"
```

### Passo 3: Instalar Dependências

```bash
# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instalar dependências básicas
pip install -r requirements.txt

# Instalar modelo spaCy para português
python -m spacy download pt_core_news_lg
```

### Passo 4: Instalar Tesseract (Opcional - para OCR)

#### Windows:
1. Baixar instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar em `C:\Program Files\Tesseract-OCR`
3. Adicionar ao PATH ou configurar em `config/config.py`:
   ```python
   TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-por  # Português
```

#### Mac:
```bash
brew install tesseract
brew install tesseract-lang  # Para português
```

### Passo 5: Configurar Banco de Dados (Opcional)

#### Instalar PostgreSQL:
- **Windows**: https://www.postgresql.org/download/windows/
- **Linux**: `sudo apt-get install postgresql postgresql-contrib`
- **Mac**: `brew install postgresql`

#### Criar banco de dados:
```sql
-- No psql ou pgAdmin
CREATE DATABASE editais_unirv;
```

#### Configurar em config/config.py:
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'editais_unirv',
    'user': 'seu_usuario',
    'password': 'sua_senha',
    'port': 5432
}
```

### Passo 6: Ajustar Configurações

Edite `config/config.py` conforme suas necessidades:

```python
class Config:
    # Cache
    CACHE_TTL_HOURS = 24  # Quanto tempo manter cache
    USE_CACHE = True      # Ativar/desativar cache
    
    # OCR
    USE_OCR = False       # True se Tesseract instalado
    
    # NLP
    USE_NLP = True        # True se spaCy instalado
    
    # Scraping
    DELAY_BETWEEN_REQUESTS = 1  # Segundos entre requisições
```

## 🚀 Como Executar

### Execução Básica
```bash
python main.py
```

### Execução com Mais Páginas
Edite `main.py` e altere:
```