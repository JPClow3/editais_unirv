import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class StructureMonitor:
    """Monitora mudanças na estrutura HTML"""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def gerar_assinatura_estrutura(self, soup: BeautifulSoup) -> Dict:
        estrutura = {
            'tags_importantes': {},
            'classes_principais': set(),
            'ids_principais': set()
        }

        elementos_chave = [
            ('article', 'tease'),
            ('h2', 'entry-title'),
            ('section', 'entry-content'),
            ('div', 'meta-date')
        ]

        for tag, classe in elementos_chave:
            elementos = soup.find_all(tag, class_=classe)
            estrutura['tags_importantes'][f"{tag}.{classe}"] = len(elementos)

        for elem in soup.find_all(True):
            if elem.get('class'):
                estrutura['classes_principais'].update(elem.get('class'))
            if elem.get('id'):
                estrutura['ids_principais'].add(elem.get('id'))

        estrutura['classes_principais'] = sorted(list(estrutura['classes_principais']))
        estrutura['ids_principais'] = sorted(list(estrutura['ids_principais']))

        return estrutura

    def detectar_mudancas(self, url: str, soup: BeautifulSoup) -> Dict:
        estrutura_atual = self.gerar_assinatura_estrutura(soup)
        estrutura_anterior = self._carregar_estrutura_anterior(url)

        if not estrutura_anterior:
            self._salvar_estrutura(url, estrutura_atual)
            return {'primeira_vez': True, 'mudancas': []}

        mudancas = self._comparar_estruturas(
            estrutura_anterior['estrutura'],
            estrutura_atual
        )

        if mudancas:
            self._salvar_estrutura(url, estrutura_atual)

        return {
            'primeira_vez': False,
            'mudancas': mudancas,
            'critico': self._avaliar_criticidade(mudancas)
        }

    def _carregar_estrutura_anterior(self, url: str) -> Optional[Dict]:
        hash_url = hashlib.md5(url.encode()).hexdigest()
        arquivo = os.path.join(self.cache_dir, f"{hash_url}.json")

        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _salvar_estrutura(self, url: str, estrutura: Dict):
        hash_url = hashlib.md5(url.encode()).hexdigest()
        arquivo = os.path.join(self.cache_dir, f"{hash_url}.json")

        dados = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'estrutura': estrutura
        }

        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2)

    def _comparar_estruturas(self, anterior: Dict, atual: Dict) -> List[Dict]:
        mudancas = []

        tags_anteriores = anterior['tags_importantes']
        tags_atuais = atual['tags_importantes']

        for tag, count_anterior in tags_anteriores.items():
            count_atual = tags_atuais.get(tag, 0)
            if count_atual != count_anterior:
                mudancas.append({
                    'tipo': 'contagem_elementos',
                    'elemento': tag,
                    'anterior': count_anterior,
                    'atual': count_atual
                })

        return mudancas

    def _avaliar_criticidade(self, mudancas: List[Dict]) -> bool:
        elementos_criticos = ['article.tease', 'h2.entry-title']

        for mudanca in mudancas:
            if mudanca['tipo'] == 'contagem_elementos':
                if mudanca['elemento'] in elementos_criticos and mudanca['atual'] == 0:
                    return True

        return False
