import requests
import re
from typing import Dict, List, Optional
from datetime import datetime
import PyPDF2
import io


class EditalPDFExtractor:
    """
    Extrai informações estruturadas de PDFs de editais
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def baixar_pdf(self, url: str) -> Optional[bytes]:
        """Baixa PDF da URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Erro ao baixar PDF {url}: {e}")
            return None

    def extrair_texto_pdf(self, pdf_bytes: bytes) -> str:
        """Extrai texto do PDF"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            texto = ""
            for page in pdf_reader.pages:
                texto += page.extract_text() + "\n"

            return texto
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def extrair_valores(self, texto: str) -> Dict:
        """Extrai informações sobre valores/recursos do edital"""
        valores = {
            'valor_total': None,
            'valor_por_projeto': None,
            'quantidade_projetos': None,
            'contrapartida': None
        }

        # Padrões para valores em reais
        padroes_valor = [
            r'R\$\s*([\d.,]+(?:\.\d{3})*(?:,\d{2})?)',
            r'valor\s+total[:\s]+R\$\s*([\d.,]+)',
            r'recursos?\s+de\s+R\$\s*([\d.,]+)',
            r'montante\s+de\s+R\$\s*([\d.,]+)'
        ]

        for padrao in padroes_valor:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            for match in matches:
                valor_str = match.group(1)
                # Converte formato brasileiro para número
                valor = float(valor_str.replace('.', '').replace(',', '.'))
                if not valores['valor_total'] or valor > valores['valor_total']:
                    valores['valor_total'] = valor

        # Quantidade de projetos
        match_projetos = re.search(r'até\s+(\d+)\s+projetos?', texto, re.IGNORECASE)
        if match_projetos:
            valores['quantidade_projetos'] = int(match_projetos.group(1))

        # Contrapartida
        if re.search(r'contrapartida', texto, re.IGNORECASE):
            match_contrapartida = re.search(
                r'contrapartida[^\d]*([\d.,]+\s*%|R\$\s*[\d.,]+)',
                texto,
                re.IGNORECASE
            )
            if match_contrapartida:
                valores['contrapartida'] = match_contrapartida.group(1)

        return valores

    def extrair_datas(self, texto: str) -> Dict:
        """Extrai datas importantes do edital"""
        datas = {
            'inscricoes_inicio': None,
            'inscricoes_fim': None,
            'resultado_preliminar': None,
            'resultado_final': None,
            'execucao_inicio': None,
            'execucao_fim': None
        }

        # Padrões de data
        padroes_data = [
            r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        ]

        meses = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }

        # Buscar seções de cronograma
        secoes_cronograma = [
            r'cronograma.*?(?=\n\n|\Z)',
            r'calendário.*?(?=\n\n|\Z)',
            r'prazo.*?(?=\n\n|\Z)'
        ]

        texto_cronograma = ""
        for padrao in secoes_cronograma:
            match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
            if match:
                texto_cronograma += match.group(0) + "\n"

        # Extrair datas de inscrição
        match_inscricao = re.search(
            r'inscrições?[^\d]*([\d/]+)\s+(?:a|até|e)\s+([\d/]+)',
            texto_cronograma or texto,
            re.IGNORECASE
        )
        if match_inscricao:
            datas['inscricoes_inicio'] = match_inscricao.group(1)
            datas['inscricoes_fim'] = match_inscricao.group(2)

        # Extrair data de resultado
        match_resultado = re.search(
            r'resultado\s+(?:preliminar|parcial)[^\d]*([\d/]+)',
            texto_cronograma or texto,
            re.IGNORECASE
        )
        if match_resultado:
            datas['resultado_preliminar'] = match_resultado.group(1)

        match_resultado_final = re.search(
            r'resultado\s+final[^\d]*([\d/]+)',
            texto_cronograma or texto,
            re.IGNORECASE
        )
        if match_resultado_final:
            datas['resultado_final'] = match_resultado_final.group(1)

        return datas

    def extrair_publico_alvo(self, texto: str) -> List[str]:
        """Identifica público-alvo do edital"""
        publico = []

        criterios = {
            'Pesquisadores': [r'pesquisador', r'docente', r'professor'],
            'Estudantes': [r'estudante', r'aluno', r'graduação', r'mestrado', r'doutorado'],
            'Empresas': [r'empresa', r'CNPJ', r'MEI', r'startup'],
            'ICTs': [r'ICT', r'instituição de ciência', r'universidade'],
            'ONGs': [r'ONG', r'organização não governamental', r'terceiro setor'],
            'Empreendedores': [r'empreendedor', r'inovador']
        }

        texto_lower = texto.lower()

        for categoria, padroes in criterios.items():
            if any(re.search(padrao, texto_lower) for padrao in padroes):
                publico.append(categoria)

        return publico if publico else ['Geral']

    def extrair_requisitos(self, texto: str) -> List[str]:
        """Extrai requisitos principais do edital"""
        requisitos = []

        # Buscar seção de requisitos
        secoes = [
            r'requisitos?.*?(?=\n[A-Z]|\Z)',
            r'critérios?.*?(?=\n[A-Z]|\Z)',
            r'condições.*?(?=\n[A-Z]|\Z)'
        ]

        for padrao in secoes:
            match = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
            if match:
                secao_texto = match.group(0)
                # Extrair itens numerados ou com bullets
                itens = re.findall(r'(?:^|\n)\s*[\d\-•]\s*([^\n]+)', secao_texto)
                requisitos.extend(itens)

        return requisitos[:10]  # Limitar a 10 principais

    def extrair_areas_tematicas(self, texto: str) -> List[str]:
        """Identifica áreas temáticas do edital"""
        areas_conhecidas = {
            'Saúde': [r'saúde', r'medicina', r'farmácia', r'enfermagem'],
            'Tecnologia': [r'tecnologia', r'TI', r'informática', r'software'],
            'Agricultura': [r'agricultura', r'agropecuária', r'rural', r'agronomia'],
            'Energia': [r'energia', r'energético', r'solar', r'eólica', r'renovável'],
            'Meio Ambiente': [r'ambiente', r'sustentabilidade', r'ecologia'],
            'Educação': [r'educação', r'ensino', r'pedagógico'],
            'Inovação': [r'inovação', r'startup', r'empreendedorismo'],
            'Ciências Sociais': [r'social', r'humanas', r'sociologia'],
            'Engenharia': [r'engenharia', r'construção', r'infraestrutura']
        }

        areas = []
        texto_lower = texto.lower()

        for area, padroes in areas_conhecidas.items():
            if any(re.search(padrao, texto_lower) for padrao in padroes):
                areas.append(area)

        return areas if areas else ['Multidisciplinar']

    def processar_edital(self, url_pdf: str) -> Dict:
        """Processa PDF completo e retorna informações estruturadas"""
        print(f"Processando PDF: {url_pdf}")

        pdf_bytes = self.baixar_pdf(url_pdf)
        if not pdf_bytes:
            return {}

        texto = self.extrair_texto_pdf(pdf_bytes)
        if not texto:
            return {}

        informacoes = {
            'url_pdf': url_pdf,
            'valores': self.extrair_valores(texto),
            'datas': self.extrair_datas(texto),
            'publico_alvo': self.extrair_publico_alvo(texto),
            'requisitos': self.extrair_requisitos(texto),
            'areas_tematicas': self.extrair_areas_tematicas(texto),
            'tamanho_texto': len(texto),
            'numero_paginas': texto.count('\n\n\n')  # Aproximação
        }

        return informacoes


# Script integrado para uso completo
def processar_editais_completo():
    """Função principal que integra scraping e extração de PDFs"""
    from fapeg_scraper import FAPEGScraper

    # 1. Coletar lista de editais
    scraper = FAPEGScraper()
    editais = scraper.coletar_todos_editais(max_paginas=2)

    # 2. Processar PDFs
    extrator = EditalPDFExtractor()

    for edital in editais:
        if edital.get('links_pdf'):
            # Processar primeiro PDF encontrado
            primeiro_pdf = edital['links_pdf'][0]['url']
            info_pdf = extrator.processar_edital(primeiro_pdf)

            # Adicionar informações extraídas
            edital['detalhes_pdf'] = info_pdf

    # 3. Salvar resultado final
    scraper.salvar_resultados(editais, 'editais_completo.json')

    return editais


if __name__ == "__main__":
    # Exemplo de uso individual
    extrator = EditalPDFExtractor()

    # Testar com um PDF específico
    url_exemplo = "https://goias.gov.br/fapeg/wp-content/uploads/sites/5/2025/09/Chamada_28_2025___Apoio_a_Manutencao_de_Equipamentos.pdf"

    resultado = extrator.processar_edital(url_exemplo)

    print("\n=== Informações Extraídas ===")
    print(f"Valores: {resultado.get('valores', {})}")
    print(f"Datas: {resultado.get('datas', {})}")
    print(f"Público-alvo: {resultado.get('publico_alvo', [])}")
    print(f"Áreas: {resultado.get('areas_tematicas', [])}")