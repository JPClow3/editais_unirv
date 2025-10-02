from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Dict


@dataclass
class Edital:
    """Modelo de dados para Edital"""
    id: Optional[int] = None
    numero_edital: Optional[str] = None
    titulo: str = ""
    url: str = ""
    entidade_principal: Optional[str] = None
    data_publicacao: Optional[date] = None
    data_atualizacao: Optional[date] = None
    status: str = "aberto"
    conteudo_completo: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'numero_edital': self.numero_edital,
            'titulo': self.titulo,
            'url': self.url,
            'entidade_principal': self.entidade_principal,
            'data_publicacao': self.data_publicacao.isoformat() if self.data_publicacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'status': self.status,
            'conteudo_completo': self.conteudo_completo
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            id=data.get('id'),
            numero_edital=data.get('numero_edital'),
            titulo=data.get('titulo', ''),
            url=data.get('url', ''),
            entidade_principal=data.get('entidade_principal'),
            data_publicacao=data.get('data_publicacao'),
            data_atualizacao=data.get('data_atualizacao'),
            status=data.get('status', 'aberto'),
            conteudo_completo=data.get('conteudo_completo')
        )


@dataclass
class EditalValor:
    """Modelo para valores do edital"""
    id: Optional[int] = None
    edital_id: Optional[int] = None
    valor_total: Optional[float] = None
    valor_por_projeto: Optional[float] = None
    quantidade_projetos: Optional[int] = None
    contrapartida: Optional[str] = None
    moeda: str = "BRL"


@dataclass
class Cronograma:
    """Modelo para cronograma"""
    id: Optional[int] = None
    edital_id: Optional[int] = None
    fase: str = ""
    descricao: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    eh_critico: bool = False


@dataclass
class Destinatario:
    """Modelo para destinatários de notificações"""
    id: Optional[int] = None
    nome: str = ""
    email: str = ""
    telefone: Optional[str] = None
    tipo: str = "docente"  # docente, estudante, gestor
    departamento: Optional[str] = None
    areas_interesse: List[str] = None
    ativo: bool = True

    def __post_init__(self):
        if self.areas_interesse is None:
            self.areas_interesse = []


class DatabaseQueries:
    """Queries SQL pré-definidas para operações comuns"""

    # ========== QUERIES DE INSERÇÃO ==========

    INSERT_EDITAL = """
                    INSERT INTO editais (numero_edital, titulo, url, entidade_principal, \
                                         data_publicacao, data_atualizacao, conteudo_completo, status) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (url) DO \
                    UPDATE SET
                        data_atualizacao = EXCLUDED.data_atualizacao, \
                        conteudo_completo = EXCLUDED.conteudo_completo, \
                        status = EXCLUDED.status \
                        RETURNING id \
                    """

    INSERT_VALOR = """
                   INSERT INTO edital_valores (edital_id, valor_total, valor_por_projeto, \
                                               quantidade_projetos, contrapartida) \
                   VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING \
                   """

    INSERT_CRONOGRAMA = """
                        INSERT INTO edital_cronograma (edital_id, fase, descricao, data_inicio, data_fim, eh_critico) \
                        VALUES (%s, %s, %s, %s, %s, %s) \
                        """

    INSERT_PUBLICO = """
                     INSERT INTO edital_publico (edital_id, categoria, detalhes)
                     VALUES (%s, %s, %s) \
                     """

    INSERT_AREA = """
                  INSERT INTO edital_areas (edital_id, area, subarea)
                  VALUES (%s, %s, %s) \
                  """

    INSERT_REQUISITO = """
                       INSERT INTO edital_requisitos (edital_id, requisito, tipo, obrigatorio, ordem) \
                       VALUES (%s, %s, %s, %s, %s) \
                       """

    INSERT_DOCUMENTO = """
                       INSERT INTO edital_documentos (edital_id, tipo, url, titulo, processado) \
                       VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING \
                       """

    INSERT_RELEVANCIA = """
                        INSERT INTO edital_relevancia (edital_id, score_total, areas_interesse, \
                                                       publico_unirv, complexidade, recomendacao) \
                        VALUES (%s, %s, %s, %s, %s, %s) \
                        """

    INSERT_NOTIFICACAO = """
                         INSERT INTO notificacoes (edital_id, tipo, destinatarios, assunto, mensagem, status) \
                         VALUES (%s, %s, %s, %s, %s, %s) RETURNING id \
                         """

    INSERT_DESTINATARIO = """
                          INSERT INTO destinatarios (nome, email, telefone, tipo, departamento, \
                                                     areas_interesse, ativo) \
                          VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO \
                          UPDATE SET
                              nome = EXCLUDED.nome, \
                              telefone = EXCLUDED.telefone, \
                              tipo = EXCLUDED.tipo, \
                              departamento = EXCLUDED.departamento, \
                              areas_interesse = EXCLUDED.areas_interesse, \
                              ativo = EXCLUDED.ativo \
                              RETURNING id \
                          """

    # ========== QUERIES DE CONSULTA ==========

    SELECT_EDITAIS_ABERTOS = """
                             SELECT e.*, \
                                    v.valor_total, \
                                    v.valor_por_projeto,
                                    array_agg(DISTINCT a.area)      as areas,
                                    array_agg(DISTINCT p.categoria) as publico_alvo
                             FROM editais e
                                      LEFT JOIN edital_valores v ON e.id = v.edital_id
                                      LEFT JOIN edital_areas a ON e.id = a.edital_id
                                      LEFT JOIN edital_publico p ON e.id = p.edital_id
                             WHERE e.status = 'aberto'
                             GROUP BY e.id, v.valor_total, v.valor_por_projeto
                             ORDER BY e.data_publicacao DESC
                                 LIMIT %s \
                             """

    SELECT_EDITAL_BY_ID = """
                          SELECT * \
                          FROM editais \
                          WHERE id = %s \
                          """

    SELECT_EDITAL_BY_URL = """
                           SELECT * \
                           FROM editais \
                           WHERE url = %s \
                           """

    SELECT_CRONOGRAMA = """
                        SELECT * \
                        FROM edital_cronograma
                        WHERE edital_id = %s
                        ORDER BY data_inicio, data_fim \
                        """

    SELECT_VALORES = """
                     SELECT * \
                     FROM edital_valores \
                     WHERE edital_id = %s \
                     """

    SELECT_REQUISITOS = """
                        SELECT * \
                        FROM edital_requisitos
                        WHERE edital_id = %s
                        ORDER BY ordem \
                        """

    SELECT_DOCUMENTOS = """
                        SELECT * \
                        FROM edital_documentos
                        WHERE edital_id = %s
                        ORDER BY data_upload DESC \
                        """

    SELECT_EDITAIS_VENCENDO = """
                              SELECT e.*, c.data_fim
                              FROM editais e
                                       JOIN edital_cronograma c ON e.id = c.edital_id
                              WHERE c.fase = 'Inscrições'
                                AND c.data_fim BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
                                AND e.status = 'aberto'
                              ORDER BY c.data_fim \
                              """

    SELECT_EDITAIS_POR_AREA = """
                              SELECT DISTINCT e.*
                              FROM editais e
                                       JOIN edital_areas a ON e.id = a.edital_id
                              WHERE a.area = ANY (%s)
                                AND e.status = 'aberto'
                              ORDER BY e.data_publicacao DESC \
                              """

    SELECT_EDITAIS_POR_PUBLICO = """
                                 SELECT DISTINCT e.*
                                 FROM editais e
                                          JOIN edital_publico p ON e.id = p.edital_id
                                 WHERE p.categoria = ANY (%s)
                                   AND e.status = 'aberto'
                                 ORDER BY e.data_publicacao DESC \
                                 """

    SELECT_DESTINATARIOS_ATIVOS = """
                                  SELECT * \
                                  FROM destinatarios
                                  WHERE ativo = true
                                  ORDER BY nome \
                                  """

    SELECT_DESTINATARIOS_POR_AREA = """
                                    SELECT * \
                                    FROM destinatarios
                                    WHERE ativo = true
                                      AND areas_interesse && %s
                                    ORDER BY nome \
                                    """

    # ========== QUERIES DE BUSCA FULL-TEXT ==========

    SEARCH_EDITAIS = """
                     SELECT e.*,
                            ts_rank(e.tsv_conteudo, query) as rank
                     FROM editais e,
                          plainto_tsquery('portuguese', %s) query
                     WHERE e.tsv_conteudo @@ query
                       AND e.status = 'aberto'
                     ORDER BY rank DESC, e.data_publicacao DESC
                         LIMIT %s \
                     """

    # ========== QUERIES DE ESTATÍSTICAS ==========

    STATS_GERAL = """
                  SELECT COUNT(*) as total_editais, \
                         COUNT(*)    FILTER (WHERE status = 'aberto') as abertos, COUNT(*) FILTER (WHERE status = 'fechado') as fechados, SUM(v.valor_total) as valor_total_disponivel
                  FROM editais e
                           LEFT JOIN edital_valores v ON e.id = v.edital_id \
                  """

    STATS_POR_ENTIDADE = """
                         SELECT entidade_principal, COUNT(*) as quantidade
                         FROM editais
                         WHERE status = 'aberto'
                         GROUP BY entidade_principal
                         ORDER BY quantidade DESC \
                         """

    STATS_POR_AREA = """
                     SELECT a.area, COUNT(DISTINCT e.id) as quantidade
                     FROM editais e
                              JOIN edital_areas a ON e.id = a.edital_id
                     WHERE e.status = 'aberto'
                     GROUP BY a.area
                     ORDER BY quantidade DESC \
                     """

    STATS_VALORES_MEDIO = """
                          SELECT AVG(valor_total) as valor_medio, \
                                 MIN(valor_total) as valor_minimo, \
                                 MAX(valor_total) as valor_maximo
                          FROM edital_valores
                          WHERE valor_total > 0 \
                          """

    # ========== QUERIES DE ATUALIZAÇÃO ==========

    UPDATE_STATUS_EDITAL = """
                           UPDATE editais
                           SET status = %s
                           WHERE id = %s \
                           """

    UPDATE_DOCUMENTO_PROCESSADO = """
                                  UPDATE edital_documentos
                                  SET processado = true
                                  WHERE id = %s \
                                  """

    # ========== QUERIES DE EXCLUSÃO ==========

    DELETE_EDITAL = """
                    DELETE \
                    FROM editais \
                    WHERE id = %s \
                    """

    DELETE_EDITAIS_ANTIGOS = """
                             DELETE \
                             FROM editais
                             WHERE data_publicacao < CURRENT_DATE - INTERVAL '%s days'
                               AND status = 'fechado' \
                             """

