import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Optional


class ResultCache:
    """Sistema de cache para resultados"""

    def __init__(self, cache_dir: str, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        os.makedirs(cache_dir, exist_ok=True)

    def _gerar_chave(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def _arquivo_cache(self, chave: str) -> str:
        return os.path.join(self.cache_dir, f"{chave}.json")

    def existe(self, url: str) -> bool:
        chave = self._gerar_chave(url)
        arquivo = self._arquivo_cache(chave)

        if not os.path.exists(arquivo):
            return False

        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        timestamp = datetime.fromisoformat(dados['timestamp'])
        horas_passadas = (datetime.now() - timestamp).total_seconds() / 3600

        return horas_passadas < self.ttl_hours

    def obter(self, url: str) -> Optional[Dict]:
        if not self.existe(url):
            return None

        chave = self._gerar_chave(url)
        arquivo = self._arquivo_cache(chave)

        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        return dados['conteudo']

    def salvar(self, url: str, conteudo: Dict):
        chave = self._gerar_chave(url)
        arquivo = self._arquivo_cache(chave)

        dados = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'conteudo': conteudo
        }

        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
