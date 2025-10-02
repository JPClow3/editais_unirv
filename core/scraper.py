import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional
import json
from urllib.parse import urljoin
import time


class FAPEGScraper:
    """Scraper básico para editais da FAPEG"""

    def __init__(self, config):
        self.base_url = config.FAPEG_BASE_URL
        self.editais_url = config.FAPEG_EDITAIS_URL
        self.config = config

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extrair_lista_editais(self, pagina: int = 1) -> List[Dict]:
        """Extrai lista de editais da página"""
        url = self.editais_url if pagina == 1 else f"{self.editais_url}page/{pagina}/"

        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            return []

        editais = []
        artigos = soup.find_all('article', class_='tease')

        for artigo in artigos:
            try:
                titulo_elem = artigo.find('h2', class_='entry-title')
                if not titulo_elem:
                    continue

                link_elem = titulo_elem.find('a')
                titulo = link_elem.get_text(strip=True)
                url_edital = link_elem.get('href')

                datas = artigo.find_all('div', class_='meta-date')
                data_publicacao = None
                data_atualizacao = None

                for data in datas:
                    texto = data.get_text(strip=True)
                    if 'Publicado em' in texto:
                        data_publicacao = data.find('span', class_='date').get_text(strip=True)
                    elif 'Última Atualização' in texto:
                        date_link = data.find('a', class_='meta-date-link')
                        if date_link:
                            data_atualizacao = date_link.get_text(strip=True).replace('Última Atualização em',
                                                                                      '').strip()

                editais.append({
                    'titulo': titulo,
                    'url': url_edital,
                    'data_publicacao': data_publicacao,
                    'data_atualizacao': data_atualizacao,
                    'numero_edital': self._extrair_numero_edital(titulo),
                    'entidade_principal': self._identificar_entidade(titulo),
                    'area_foco': self._identificar_area_foco(titulo),
                    'tipo_apoio': self._identificar_tipo_apoio(titulo)
                })

            except Exception as e:
                print(f"Erro ao processar artigo: {e}")
                continue

        return editais

    def extrair_detalhes_edital(self, url: str) -> Dict:
        """Extrai detalhes de um edital específico"""
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            return {}

        detalhes = {
            'url': url,
            'links_pdf': [],
            'links_anexos': [],
            'links_resultados': [],
            'conteudo_texto': ''
        }

        entry_content = soup.find('section', class_='entry-content')

        if entry_content:
            links = entry_content.find_all('a')

            for link in links:
                href = link.get('href')
                texto = link.get_text(strip=True).lower()

                if href:
                    href_absoluto = urljoin(self.base_url, href)

                    if href.endswith('.pdf'):
                        detalhes['links_pdf'].append({
                            'url': href_absoluto,
                            'texto': link.get_text(strip=True)
                        })
                    elif any(palavra in texto for palavra in ['resultado', 'retificação']):
                        detalhes['links_resultados'].append({
                            'url': href_absoluto,
                            'texto': link.get_text(strip=True)
                        })
                    elif any(palavra in texto for palavra in ['anexo', 'formulário']):
                        detalhes['links_anexos'].append({
                            'url': href_absoluto,
                            'texto': link.get_text(strip=True)
                        })

            detalhes['conteudo_texto'] = entry_content.get_text(strip=True, separator=' ')

        return detalhes

    def _extrair_numero_edital(self, titulo: str) -> Optional[str]:
        match = re.search(r'n[oº°]\s*(\d+/\d+)', titulo, re.IGNORECASE)
        return match.group(1) if match else None

    def _identificar_entidade(self, titulo_ou_url: str) -> str:
        texto = titulo_ou_url.upper()

        entidades = {
            'FAPEG': ['FAPEG'],
            'FINEP': ['FINEP'],
            'SEBRAE': ['SEBRAE'],
            'SECTI': ['SECTI']
        }

        entidades_encontradas = []
        for entidade, palavras in entidades.items():
            if any(palavra in texto for palavra in palavras):
                entidades_encontradas.append(entidade)

        return '/'.join(entidades_encontradas) if entidades_encontradas else 'FAPEG'

    def _identificar_area_foco(self, titulo: str) -> List[str]:
        areas = {
            'Inovação': ['inovação', 'empreendimentos'],
            'Pesquisa': ['pesquisa', 'científico'],
            'Infraestrutura': ['laboratório', 'equipamento'],
            'Mobilidade': ['mobilidade', 'internacional'],
            'Energia': ['energia', 'energética']
        }

        titulo_lower = titulo.lower()
        areas_identificadas = []

        for area, palavras in areas.items():
            if any(palavra in titulo_lower for palavra in palavras):
                areas_identificadas.append(area)

        return areas_identificadas if areas_identificadas else ['Geral']

    def _identificar_tipo_apoio(self, titulo: str) -> str:
        titulo_lower = titulo.lower()

        if 'bolsa' in titulo_lower:
            return 'Bolsa'
        elif 'fomento' in titulo_lower or 'auxílio' in titulo_lower:
            return 'Financiamento'
        elif 'infraestrutura' in titulo_lower:
            return 'Infraestrutura'

        return 'Apoio Geral'

    def coletar_todos_editais(self, max_paginas: int = 5) -> List[Dict]:
        """Coleta editais de múltiplas páginas"""
        todos_editais = []

        for pagina in range(1, max_paginas + 1):
            print(f"\nProcessando página {pagina}...")

            editais_basicos = self.extrair_lista_editais(pagina)

            if not editais_basicos:
                break

            print(f"Encontrados {len(editais_basicos)} editais")

            for edital in editais_basicos:
                try:
                    detalhes = self.extrair_detalhes_edital(edital['url'])
                    edital.update(detalhes)
                    todos_editais.append(edital)
                    time.sleep(self.config.DELAY_BETWEEN_REQUESTS)
                except Exception as e:
                    print(f"Erro: {e}")

        return todos_editais