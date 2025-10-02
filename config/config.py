import os


class Config:
    """Configurações centralizadas do projeto"""

    # Diretórios
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CACHE_DIR = os.path.join(BASE_DIR, 'cache_resultados')
    STRUCTURE_CACHE_DIR = os.path.join(BASE_DIR, 'cache_estrutura')

    # URLs
    FAPEG_BASE_URL = "https://goias.gov.br/fapeg"
    FAPEG_EDITAIS_URL = "https://goias.gov.br/fapeg/categoria/editais/"

    # Cache
    CACHE_TTL_HOURS = 24
    USE_CACHE = True

    # Scraping
    REQUEST_TIMEOUT = 30
    DELAY_BETWEEN_REQUESTS = 1  # segundos
    MAX_RETRIES = 3

    # OCR
    USE_OCR = True
    TESSERACT_CMD = None

    # Database
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'editais_unirv',
        'user': 'postgres',
        'password': 'postgresUNIRV',
        'port': 5432
    }

    # NLP
    USE_NLP = True
    SPACY_MODEL = 'pt_core_news_lg'

    # UniRV - Áreas de interesse
    UNIRV_AREAS_INTERESSE = [
        'agronomia', 'saude', 'tecnologia',
        'educacao', 'meio_ambiente', 'inovacao'
    ]