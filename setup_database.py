from config.config import Config
from database.db_manager import EditalDatabase


def criar_banco():
    """Cria schema do banco de dados"""

    config = Config()

    print("Conectando ao banco de dados...")
    db = EditalDatabase(config.DB_CONFIG)
    db.conectar()

    print("Criando schema...")
    db.criar_schema()

    print("\nSchema criado com sucesso!")
    print("Banco de dados pronto para uso.")

    db.fechar()


if __name__ == "__main__":
    criar_banco()