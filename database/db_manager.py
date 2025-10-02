from typing import Dict, Any, List, Optional

import psycopg2
from psycopg2 import extras

from database.models import (Edital, EditalValor, Cronograma, Destinatario,
                             DatabaseQueries as Queries)


class EditalDatabase:
    """Gerenciador de banco de dados para editais."""

    def __init__(self, db_config: Dict[str, Any]):
        """
        Inicializa o gerenciador do banco de dados.

        Args:
            db_config: Dicionário com as configurações de conexão.
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def conectar(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor)
        except psycopg2.OperationalError as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def fechar(self):
        """Fecha a conexão com o banco de dados."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def _executar_query(self, query: str, params: tuple = None, fetch: str = None):
        """
        Executa uma query no banco de dados.

        Args:
            query: A query SQL a ser executada.
            params: Os parâmetros para a query.
            fetch: O tipo de fetch a ser realizado ('one', 'all').

        Returns:
            O resultado da query, se houver.
        """
        if not self.conn or self.conn.closed:
            self.conectar()

        try:
            self.cursor.execute(query, params)

            if fetch == 'one':
                return self.cursor.fetchone()
            elif fetch == 'all':
                return self.cursor.fetchall()
            else:
                self.conn.commit()
                # Para INSERT ... RETURNING id
                if "RETURNING id" in query.upper():
                    return self.cursor.fetchone()
                return None
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"Erro ao executar a query: {e}")
            return None

    def criar_schema(self):
        """Cria as tabelas do banco de dados se não existirem."""

        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS editais (
                id SERIAL PRIMARY KEY,
                numero_edital VARCHAR(50),
                titulo TEXT NOT NULL,
                url VARCHAR(255) UNIQUE NOT NULL,
                entidade_principal VARCHAR(100),
                data_publicacao DATE,
                data_atualizacao DATE,
                conteudo_completo JSONB,
                status VARCHAR(20) DEFAULT 'aberto',
                tsv_conteudo tsvector,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_editais_status ON editais (status);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tsv_conteudo ON editais USING GIN(tsv_conteudo);
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_valores (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                valor_total NUMERIC(15, 2),
                valor_por_projeto NUMERIC(15, 2),
                quantidade_projetos INTEGER,
                contrapartida TEXT,
                moeda VARCHAR(10) DEFAULT 'BRL'
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_cronograma (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                fase VARCHAR(100) NOT NULL,
                descricao TEXT,
                data_inicio DATE,
                data_fim DATE,
                eh_critico BOOLEAN DEFAULT FALSE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_publico (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                categoria VARCHAR(100),
                detalhes TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_areas (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                area VARCHAR(100),
                subarea VARCHAR(100)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_requisitos (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                requisito TEXT NOT NULL,
                tipo VARCHAR(50),
                obrigatorio BOOLEAN DEFAULT TRUE,
                ordem INTEGER
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_documentos (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                tipo VARCHAR(50),
                url VARCHAR(255) UNIQUE NOT NULL,
                titulo TEXT,
                processado BOOLEAN DEFAULT FALSE,
                data_upload TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS edital_relevancia (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                score_total INTEGER,
                areas_interesse JSONB,
                publico_unirv JSONB,
                complexidade VARCHAR(50),
                recomendacao TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS destinatarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                telefone VARCHAR(20),
                tipo VARCHAR(50) DEFAULT 'docente',
                departamento VARCHAR(100),
                areas_interesse TEXT[],
                ativo BOOLEAN DEFAULT TRUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS notificacoes (
                id SERIAL PRIMARY KEY,
                edital_id INTEGER REFERENCES editais(id) ON DELETE CASCADE,
                tipo VARCHAR(50),
                destinatarios JSONB,
                assunto TEXT,
                mensagem TEXT,
                status VARCHAR(20) DEFAULT 'pendente',
                data_envio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        for query in schema_queries:
            self._executar_query(query)

    # ========== MÉTODOS DE INSERÇÃO ==========

    def inserir_edital(self, edital: Edital) -> Optional[int]:
        """Insere ou atualiza um edital."""
        params = (
            edital.numero_edital, edital.titulo, edital.url,
            edital.entidade_principal, edital.data_publicacao,
            edital.data_atualizacao, psycopg2.extras.Json(edital.conteudo_completo),
            edital.status
        )
        result = self._executar_query(Queries.INSERT_EDITAL, params)
        return result['id'] if result else None

    def inserir_valor(self, valor: EditalValor):
        """Insere os valores de um edital."""
        params = (
            valor.edital_id, valor.valor_total, valor.valor_por_projeto,
            valor.quantidade_projetos, valor.contrapartida
        )
        self._executar_query(Queries.INSERT_VALOR, params)

    def inserir_cronograma(self, cronograma: Cronograma):
        """Insere uma fase do cronograma."""
        params = (
            cronograma.edital_id, cronograma.fase, cronograma.descricao,
            cronograma.data_inicio, cronograma.data_fim, cronograma.eh_critico
        )
        self._executar_query(Queries.INSERT_CRONOGRAMA, params)

    def inserir_destinatario(self, destinatario: Destinatario) -> Optional[int]:
        """Insere ou atualiza um destinatário."""
        params = (
            destinatario.nome, destinatario.email, destinatario.telefone,
            destinatario.tipo, destinatario.departamento,
            destinatario.areas_interesse, destinatario.ativo
        )
        result = self._executar_query(Queries.INSERT_DESTINATARIO, params)
        return result['id'] if result else None

    # ========== MÉTODOS DE CONSULTA ==========

    def obter_editais_abertos(self, limit: int = 20) -> List[Dict]:
        """Obtém os editais abertos mais recentes."""
        return self._executar_query(Queries.SELECT_EDITAIS_ABERTOS, (limit,), fetch='all')

    def obter_edital_por_id(self, edital_id: int) -> Optional[Dict]:
        """Obtém um edital pelo seu ID."""
        return self._executar_query(Queries.SELECT_EDITAL_BY_ID, (edital_id,), fetch='one')

    def obter_edital_por_url(self, url: str) -> Optional[Dict]:
        """Obtém um edital pela sua URL."""
        return self._executar_query(Queries.SELECT_EDITAL_BY_URL, (url,), fetch='one')

    def obter_cronograma_por_edital(self, edital_id: int) -> List[Dict]:
        """Obtém o cronograma de um edital."""
        return self._executar_query(Queries.SELECT_CRONOGRAMA, (edital_id,), fetch='all')

    def obter_destinatarios_ativos(self) -> List[Destinatario]:
        """Obtém todos os destinatários ativos."""
        rows = self._executar_query(Queries.SELECT_DESTINATARIOS_ATIVOS, fetch='all')
        return [Destinatario(**row) for row in rows] if rows else []

    def obter_destinatarios_por_area(self, areas: List[str]) -> List[Destinatario]:
        """Obtém destinatários ativos por área de interesse."""
        rows = self._executar_query(Queries.SELECT_DESTINATARIOS_POR_AREA, (areas,), fetch='all')
        return [Destinatario(**row) for row in rows] if rows else []

    # ========== MÉTODOS DE ATUALIZAÇÃO ==========

    def atualizar_status_edital(self, edital_id: int, status: str):
        """Atualiza o status de um edital."""
        self._executar_query(Queries.UPDATE_STATUS_EDITAL, (status, edital_id))

    def marcar_documento_processado(self, documento_id: int):
        """Marca um documento como processado."""
        self._executar_query(Queries.UPDATE_DOCUMENTO_PROCESSADO, (documento_id,))

    # ========== MÉTODOS DE EXCLUSÃO ==========

    def deletar_edital(self, edital_id: int):
        """Deleta um edital e seus dados relacionados (via cascade)."""
        self._executar_query(Queries.DELETE_EDITAL, (edital_id,))


if __name__ == '__main__':
    # Exemplo de uso (requer config.py no path)
    from config.config import Config

    print("Testando o EditalDatabase...")
    try:
        config = Config()
        db = EditalDatabase(config.DB_CONFIG)
        db.conectar()
        print("Conexão bem-sucedida!")

        print("Criando/Verificando schema...")
        db.criar_schema()
        print("Schema OK.")

        # Teste de inserção e consulta
        print("Testando inserção de destinatário...")
        novo_dest = Destinatario(
            nome="Admin Teste",
            email="admin.teste@unirv.edu.br",
            tipo="gestor",
            areas_interesse=['tecnologia', 'inovacao']
        )
        dest_id = db.inserir_destinatario(novo_dest)
        print(f"Destinatário inserido com ID: {dest_id}")

        print("\nConsultando destinatários ativos...")
        destinatarios = db.obter_destinatarios_ativos()
        print(f"Total de destinatários ativos: {len(destinatarios)}")
        for d in destinatarios[:2]: # Imprime os 2 primeiros
            print(f" - {d.nome} ({d.email})")


    except Exception as e:
        print(f"Ocorreu um erro nos testes: {e}")
    finally:
        if 'db' in locals() and db.conn:
            db.fechar()
            print("\nConexão fechada.")