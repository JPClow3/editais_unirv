import sys
from config.config import Config
from core.scraper import FAPEGScraper
from core.pdf_extractor import EditalPDFExtractor
from core.nlp_analyzer import EditalNLPAnalyzer
from utils.cache import ResultCache
from utils.structure_monitor import StructureMonitor
import json


def main():
    """Script principal de execução"""

    print("=== Sistema de Coleta de Editais FAPEG - UniRV ===\n")

    # Inicializar componentes
    config = Config()
    scraper = FAPEGScraper(config)

    # Cache
    cache = None
    if config.USE_CACHE:
        cache = ResultCache(config.CACHE_DIR, config.CACHE_TTL_HOURS)
        print(f"Cache ativado (TTL: {config.CACHE_TTL_HOURS}h)")

    # 1. Coletar editais
    print("\n[1/3] Coletando lista de editais...")
    editais = scraper.coletar_todos_editais(max_paginas=3)
    print(f"Total coletado: {len(editais)} editais")

    # 2. Processar PDFs (se disponível)
    if config.USE_OCR:
        print("\n[2/3] Processando PDFs com OCR...")
        pdf_extractor = EditalPDFExtractor()

        for i, edital in enumerate(editais, 1):
            if edital.get('links_pdf'):
                print(f"  {i}/{len(editais)}: {edital['titulo'][:50]}...")
                try:
                    primeiro_pdf = edital['links_pdf'][0]['url']

                    # Verificar cache
                    if cache and cache.existe(primeiro_pdf):
                        info_pdf = cache.obter(primeiro_pdf)
                    else:
                        info_pdf = pdf_extractor.processar_edital(primeiro_pdf)
                        if cache:
                            cache.salvar(primeiro_pdf, info_pdf)

                    edital['detalhes_pdf'] = info_pdf
                except Exception as e:
                    print(f"    Erro: {e}")

    # 3. Análise NLP (se disponível)
    if config.USE_NLP:
        print("\n[3/3] Análise NLP...")
        try:
            nlp = EditalNLPAnalyzer()

            for edital in editais:
                if edital.get('conteudo_texto'):
                    relevancia = nlp.classificar_relevancia_unirv(
                        edital['conteudo_texto']
                    )
                    edital['relevancia_unirv'] = relevancia
        except Exception as e:
            print(f"NLP não disponível: {e}")

    # 4. Salvar resultados
    arquivo_saida = 'editais_unirv_completo.json'
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(editais, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Resultados salvos em: {arquivo_saida}")

    # 5. Estatísticas
    print("\n=== ESTATÍSTICAS ===")
    print(f"Total de editais: {len(editais)}")
    print(f"Com PDF: {sum(1 for e in editais if e.get('links_pdf'))}")
    print(f"Com análise completa: {sum(1 for e in editais if e.get('detalhes_pdf'))}")

    if config.USE_NLP:
        alta_relevancia = sum(
            1 for e in editais
            if e.get('relevancia_unirv', {}).get('score_total', 0) >= 40
        )
        print(f"Alta relevância para UniRV: {alta_relevancia}")


if __name__ == "__main__":
    main()