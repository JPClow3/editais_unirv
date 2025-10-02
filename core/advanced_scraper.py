# ============================================================================
# ARQUIVO: database/models.py
# Schema e queries do banco de dados
# ============================================================================

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


# ============================================================================
# ARQUIVO: core/advanced_scraper.py
# Scraper avançado com OCR e monitoramento
# ============================================================================

import requests
from bs4 import BeautifulSoup
import time
from typing import Dict
from urllib.parse import urljoin

# Imports de outros módulos do projeto
from config.config import Config
from utils.cache import ResultCache
from utils.structure_monitor import StructureMonitor

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image, ImageEnhance

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class AdvancedPDFExtractor:
    """Extrator de PDF com suporte a OCR"""

    def __init__(self, config: Config):
        self.config = config

        if config.USE_OCR and not OCR_AVAILABLE:
            print("AVISO: OCR solicitado mas bibliotecas não instaladas")
            print("Instale: pip install pytesseract pdf2image pillow")

        if config.USE_OCR and config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

    def extrair_texto(self, pdf_bytes: bytes) -> str:
        """Extrai texto do PDF, usando OCR se necessário"""

        # Tentar extração normal primeiro
        texto = self._extrair_texto_normal(pdf_bytes)

        # Se extraiu pouco texto, tentar OCR
        if len(texto.strip()) < 100 and self.config.USE_OCR and OCR_AVAILABLE:
            print("  Usando OCR...")
            texto = self._extrair_texto_ocr(pdf_bytes)

        return texto

    def _extrair_texto_normal(self, pdf_bytes: bytes) -> str:
        """Extração normal de PDF"""
        if not PDF_AVAILABLE:
            return ""

        try:
            import io
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            texto = ""
            for page in pdf_reader.pages:
                texto += page.extract_text() + "\n"

            return texto
        except Exception as e:
            print(f"  Erro na extração normal: {e}")
            return ""

    def _extrair_texto_ocr(self, pdf_bytes: bytes) -> str:
        """Extração com OCR"""
        if not OCR_AVAILABLE:
            return ""

        try:
            # Converter PDF para imagens
            imagens = convert_from_bytes(pdf_bytes, dpi=300)

            texto_completo = ""

            for i, imagem in enumerate(imagens, 1):
                print(f"    Página {i}/{len(imagens)}...")

                # Pré-processar imagem
                imagem = self._preprocessar_imagem(imagem)

                # OCR
                texto = pytesseract.image_to_string(
                    imagem,
                    lang='por',
                    config='--psm 6'
                )

                texto_completo += texto + "\n\n"

            return texto_completo

        except Exception as e:
            print(f"  Erro no OCR: {e}")
            return ""

    def _preprocessar_imagem(self, imagem: Image.Image) -> Image.Image:
        """Melhora qualidade da imagem para OCR"""
        # Escala de cinza
        imagem = imagem.convert('L')

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(imagem)
        imagem = enhancer.enhance(2)

        # Aumentar nitidez
        enhancer = ImageEnhance.Sharpness(imagem)
        imagem = enhancer.enhance(1.5)

        return imagem


class AdvancedFAPEGScraper:
    """
    Scraper avançado com todas as funcionalidades:
    - Cache inteligente
    - Monitoramento de estrutura HTML
    - Suporte a OCR
    - Detecção de mudanças
    """

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.FAPEG_BASE_URL
        self.editais_url = config.FAPEG_EDITAIS_URL

        # Session HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Componentes avançados
        self.cache = ResultCache(
            config.CACHE_DIR,
            config.CACHE_TTL_HOURS
        ) if config.USE_CACHE else None

        self.monitor = StructureMonitor(config.STRUCTURE_CACHE_DIR)

        self.pdf_extractor = AdvancedPDFExtractor(config)

    def coletar_com_monitoramento(
            self,
            url: str,
            tipo: str = 'pagina'
    ) -> Dict:
        """
        Coleta dados com monitoramento de estrutura e cache

        Args:
            url: URL para coletar
            tipo: 'pagina' ou 'edital'
        """
        # Verificar cache primeiro
        if self.cache and self.cache.existe(url):
            print(f"  [CACHE] {url[:60]}...")
            return self.cache.obter(url)

        # Fazer requisição
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"  Erro ao acessar {url}: {e}")
            return {}

        # Monitorar mudanças na estrutura
        resultado_monitor = self.monitor.detectar_mudancas(url, soup)

        if resultado_monitor.get('critico'):
            print(f"\n⚠️  ALERTA CRÍTICO: Mudanças na estrutura detectadas!")
            print(f"URL: {url}")
            print(f"Mudanças: {resultado_monitor['mudancas']}")
            print("O scraper pode precisar de atualização!\n")

        # Processar conteúdo
        if tipo == 'pagina':
            dados = self._processar_pagina_lista(soup)
        else:  # edital
            dados = self._processar_pagina_edital(soup, url)

        # Adicionar info de monitoramento
        dados['_monitoramento'] = resultado_monitor
        dados['_url'] = url
        dados['_coletado_em'] = time.time()

        # Salvar no cache
        if self.cache:
            self.cache.salvar(url, dados)

        return dados

    def _processar_pagina_lista(self, soup: BeautifulSoup) -> Dict:
        """Processa página de lista de editais"""
        editais = []
        artigos = soup.find_all('article', class_='tease')

        for artigo in artigos:
            try:
                titulo_elem = artigo.find('h2', class_='entry-title')
                if not titulo_elem:
                    continue

                link = titulo_elem.find('a')
                editais.append({
                    'titulo': link.get_text(strip=True),
                    'url': link.get('href')
                })
            except Exception as e:
                print(f"  Erro ao processar artigo: {e}")

        return {'editais': editais, 'quantidade': len(editais)}

    def _processar_pagina_edital(self, soup: BeautifulSoup, url: str) -> Dict:
        """Processa página individual de edital"""
        dados = {
            'url': url,
            'links_pdf': [],
            'links_anexos': [],
            'conteudo_texto': ''
        }

        entry_content = soup.find('section', class_='entry-content')

        if entry_content:
            # Extrair links
            for link in entry_content.find_all('a'):
                href = link.get('href')
                if href:
                    href_absoluto = urljoin(self.base_url, href)
                    texto = link.get_text(strip=True)

                    if href.endswith('.pdf'):
                        dados['links_pdf'].append({
                            'url': href_absoluto,
                            'texto': texto
                        })
                    else:
                        dados['links_anexos'].append({
                            'url': href_absoluto,
                            'texto': texto
                        })

            # Extrair texto
            dados['conteudo_texto'] = entry_content.get_text(strip=True, separator=' ')

        return dados

    def processar_pdf(self, url_pdf: str) -> Dict:
        """Processa PDF com cache e OCR"""
        # Verificar cache
        if self.cache and self.cache.existe(url_pdf):
            return self.cache.obter(url_pdf)

        # Baixar PDF
        try:
            response = self.session.get(url_pdf, timeout=self.config.REQUEST_TIMEOUT)
            pdf_bytes = response.content
        except Exception as e:
            print(f"  Erro ao baixar PDF: {e}")
            return {}

        # Extrair texto
        texto = self.pdf_extractor.extrair_texto(pdf_bytes)

        resultado = {
            'url': url_pdf,
            'texto': texto,
            'tamanho': len(texto),
            'metodo': 'ocr' if len(texto) > 100 and self.config.USE_OCR else 'normal'
        }

        # Salvar no cache
        if self.cache:
            self.cache.salvar(url_pdf, resultado)

        return resultado

    def estatisticas_cache(self) -> Dict:
        """Retorna estatísticas do cache"""
        if not self.cache:
            return {'cache_ativo': False}

        import os

        total = 0
        validos = 0
        tamanho = 0

        for arquivo in os.listdir(self.cache.cache_dir):
            caminho = os.path.join(self.cache.cache_dir, arquivo)
            total += 1
            tamanho += os.path.getsize(caminho)

            if self.cache.existe(arquivo.replace('.json', '')):
                validos += 1

        return {
            'cache_ativo': True,
            'total_itens': total,
            'itens_validos': validos,
            'tamanho_mb': round(tamanho / (1024 * 1024), 2),
            'ttl_hours': self.cache.ttl_hours
        }

