import re
from typing import List, Dict

import spacy


class EditalNLPAnalyzer:
    """
    Análise NLP para extração inteligente de requisitos e informações
    """

    def __init__(self):
        # Carregar modelo em português
        # pip install spacy
        # python -m spacy download pt_core_news_lg
        try:
            self.nlp = spacy.load("pt_core_news_lg")
        except:
            print("Modelo spaCy não encontrado. Instalando...")
            print("Execute: python -m spacy download pt_core_news_lg")
            self.nlp = None

    def extrair_requisitos_nlp(self, texto: str) -> List[Dict]:
        """Extrai requisitos usando NLP"""
        if not self.nlp:
            return self._extrair_requisitos_regex(texto)

        doc = self.nlp(texto)
        requisitos = []

        # Padrões de sentenças que indicam requisitos
        palavras_chave_requisitos = [
            'deve', 'deverá', 'precisa', 'necessário', 'obrigatório',
            'exigido', 'requisito', 'critério', 'condição', 'elegível'
        ]

        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_lower = sent_text.lower()

            # Verificar se é um requisito
            if any(palavra in sent_lower for palavra in palavras_chave_requisitos):
                requisito = {
                    'texto': sent_text,
                    'tipo': self._classificar_requisito(sent_text),
                    'entidades': self._extrair_entidades(sent),
                    'obrigatorio': self._eh_obrigatorio(sent_text)
                }
                requisitos.append(requisito)

        return requisitos

    def _classificar_requisito(self, texto: str) -> str:
        """Classifica tipo de requisito"""
        texto_lower = texto.lower()

        classificacao = {
            'vinculo': ['vinculado', 'vínculo', 'lotação', 'servidor', 'docente'],
            'titulacao': ['doutor', 'mestre', 'graduado', 'pós-graduação', 'titulação'],
            'experiencia': ['experiência', 'atuação', 'anos de'],
            'documentacao': ['documento', 'comprovante', 'certificado', 'declaração'],
            'financeiro': ['cnpj', 'cpf', 'conta bancária', 'regularidade fiscal'],
            'tecnico': ['lattes', 'publicações', 'projeto', 'proposta']
        }

        for tipo, palavras in classificacao.items():
            if any(palavra in texto_lower for palavra in palavras):
                return tipo

        return 'geral'

    def _extrair_entidades(self, sent) -> List[Dict]:
        """Extrai entidades nomeadas da sentença"""
        entidades = []

        for ent in sent.ents:
            entidades.append({
                'texto': ent.text,
                'tipo': ent.label_,
                'descricao': spacy.explain(ent.label_)
            })

        return entidades

    def _eh_obrigatorio(self, texto: str) -> bool:
        """Determina se requisito é obrigatório"""
        palavras_obrigatorias = [
            'obrigatório', 'deve', 'deverá', 'necessário',
            'exigido', 'imprescindível'
        ]

        texto_lower = texto.lower()
        return any(palavra in texto_lower for palavra in palavras_obrigatorias)

    def _extrair_requisitos_regex(self, texto: str) -> List[Dict]:
        """Fallback: extração por regex quando spaCy não disponível"""
        requisitos = []

        # Buscar seções de requisitos
        secoes = re.split(r'\n\s*\n', texto)

        for secao in secoes:
            if any(palavra in secao.lower() for palavra in ['requisito', 'condição', 'elegib']):
                # Extrair itens numerados ou com bullets
                itens = re.findall(r'(?:^|\n)\s*[\d\-•]\s*([^\n]+)', secao)

                for item in itens:
                    requisitos.append({
                        'texto': item.strip(),
                        'tipo': self._classificar_requisito(item),
                        'obrigatorio': self._eh_obrigatorio(item)
                    })

        return requisitos

    def extrair_perfil_beneficiario(self, texto: str) -> Dict:
        """Extrai perfil detalhado do beneficiário"""
        perfil = {
            'publico_alvo': [],
            'titulacao_minima': None,
            'vinculo_institucional': None,
            'areas_atuacao': [],
            'restricoes': []
        }

        if not self.nlp:
            return perfil

        doc = self.nlp(texto)

        # Identificar público-alvo
        padroes_publico = {
            'pesquisadores': ['pesquisador', 'cientista'],
            'docentes': ['docente', 'professor'],
            'estudantes': ['estudante', 'aluno', 'discente'],
            'empresas': ['empresa', 'cnpj', 'mei'],
            'empreendedores': ['empreendedor', 'startup']
        }

        for tipo, palavras in padroes_publico.items():
            if any(palavra in texto.lower() for palavra in palavras):
                perfil['publico_alvo'].append(tipo)

        # Titulação mínima
        titulacoes = ['doutorado', 'mestrado', 'graduação', 'especialização']
        for tit in titulacoes:
            if tit in texto.lower():
                perfil['titulacao_minima'] = tit
                break

        # Vínculo institucional
        if any(palavra in texto.lower() for palavra in ['ict', 'universidade', 'instituição']):
            perfil['vinculo_institucional'] = 'ICT'

        return perfil

    def extrair_cronograma_estruturado(self, texto: str) -> Dict:
        """Extrai cronograma estruturado"""
        cronograma = {
            'fases': [],
            'datas_importantes': {}
        }

        # Padrões de datas
        padrao_data = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'

        # Buscar seção de cronograma
        match_cronograma = re.search(
            r'cronograma.*?(?=\n\s*\d+\.|ANEXO|$)',
            texto,
            re.IGNORECASE | re.DOTALL
        )

        if match_cronograma:
            texto_cronograma = match_cronograma.group(0)

            # Extrair fases com datas
            fases = re.findall(
                r'(?:^|\n)\s*[\d\-•]\s*([^:]+):\s*([^\n]+)',
                texto_cronograma
            )

            for fase, info in fases:
                datas = re.findall(padrao_data, info)

                cronograma['fases'].append({
                    'nome': fase.strip(),
                    'descricao': info.strip(),
                    'datas': [f"{d[0]}/{d[1]}/{d[2]}" for d in datas]
                })

        # Datas importantes específicas
        padroes_datas = {
            'inscricoes_inicio': r'inscrições.*?de\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            'inscricoes_fim': r'até\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
            'resultado': r'resultado.*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})'
        }

        for chave, padrao in padroes_datas.items():
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                cronograma['datas_importantes'][chave] = match.group(1)

        return cronograma

    def classificar_relevancia_unirv(self, texto: str) -> Dict:
        """
        Classifica relevância do edital para UniRV
        """
        score = {
            'score_total': 0,
            'areas_interesse': [],
            'publico_unirv': [],
            'complexidade': 'media',
            'recomendacao': ''
        }

        # Áreas de interesse da UniRV
        areas_unirv = {
            'agronomia': ['agricultura', 'agronomia', 'rural', 'agropecuária'],
            'saude': ['saúde', 'medicina', 'enfermagem', 'farmácia'],
            'tecnologia': ['tecnologia', 'inovação', 'software', 'ti'],
            'educacao': ['educação', 'ensino', 'pedagógico'],
            'meio_ambiente': ['ambiente', 'sustentabilidade']
        }

        texto_lower = texto.lower()

        # Verificar áreas
        for area, palavras in areas_unirv.items():
            if any(palavra in texto_lower for palavra in palavras):
                score['areas_interesse'].append(area)
                score['score_total'] += 20

        # Público UniRV
        if 'docente' in texto_lower or 'professor' in texto_lower:
            score['publico_unirv'].append('docentes')
            score['score_total'] += 15

        if 'estudante' in texto_lower or 'aluno' in texto_lower:
            score['publico_unirv'].append('estudantes')
            score['score_total'] += 15

        if 'universidade' in texto_lower or 'ict' in texto_lower:
            score['publico_unirv'].append('instituicao')
            score['score_total'] += 10

        # Avaliar complexidade
        requisitos = len(re.findall(r'requisito|condição|exigência', texto_lower))
        if requisitos > 10:
            score['complexidade'] = 'alta'
        elif requisitos < 5:
            score['complexidade'] = 'baixa'

        # Gerar recomendação
        if score['score_total'] >= 40:
            score['recomendacao'] = 'ALTA - Amplamente divulgar'
        elif score['score_total'] >= 20:
            score['recomendacao'] = 'MÉDIA - Divulgar para áreas específicas'
        else:
            score['recomendacao'] = 'BAIXA - Avaliar relevância'

        return score

    def gerar_resumo_executivo(self, edital: Dict) -> str:
        """Gera resumo executivo para divulgação"""
        template = f"""
RESUMO EXECUTIVO - {edital.get('titulo', 'Edital')}

📋 NÚMERO: {edital.get('numero_edital', 'N/A')}
🏛️ INSTITUIÇÃO: {edital.get('entidade_principal', 'FAPEG')}
📅 PUBLICAÇÃO: {edital.get('data_publicacao', 'N/A')}

💰 RECURSOS DISPONÍVEIS:
- Valor Total: R$ {edital.get('detalhes_pdf', {}).get('valores', {}).get('valor_total', 'A definir')}
- Por Projeto: R$ {edital.get('detalhes_pdf', {}).get('valores', {}).get('valor_por_projeto', 'A definir')}
- Quantidade: {edital.get('detalhes_pdf', {}).get('valores', {}).get('quantidade_projetos', 'A definir')} projetos

👥 PÚBLICO-ALVO:
{', '.join(edital.get('detalhes_pdf', {}).get('publico_alvo', ['A definir']))}

📆 DATAS IMPORTANTES:
- Inscrições: {edital.get('detalhes_pdf', {}).get('datas', {}).get('inscricoes_fim', 'Consultar edital')}
- Resultado: {edital.get('detalhes_pdf', {}).get('datas', {}).get('resultado_final', 'Consultar edital')}

🔗 MAIS INFORMAÇÕES:
{edital.get('url', 'N/A')}

---
Este resumo foi gerado automaticamente pelo NIT/UniRV
"""
        return template


# Exemplo de uso integrado
if __name__ == "__main__":
    analyzer = EditalNLPAnalyzer()

    # Texto de exemplo
    texto_exemplo = """
    REQUISITOS PARA PARTICIPAÇÃO

    1. O proponente deve ser docente vinculado a instituição de ensino superior em Goiás
    2. É necessário possuir titulação mínima de doutorado
    3. Ter experiência comprovada de pelo menos 2 anos na área
    4. Apresentar currículo Lattes atualizado
    5. As inscrições serão realizadas de 01/10/2025 até 30/10/2025
    6. Resultado final será divulgado em 15/12/2025
    """

    # Extrair requisitos
    requisitos = analyzer.extrair_requisitos_nlp(texto_exemplo)

    print("=== REQUISITOS EXTRAÍDOS ===")
    for req in requisitos:
        print(f"\n• {req['texto']}")
        print(f"  Tipo: {req['tipo']}")
        print(f"  Obrigatório: {'Sim' if req['obrigatorio'] else 'Não'}")

    # Extrair perfil
    perfil = analyzer.extrair_perfil_beneficiario(texto_exemplo)
    print(f"\n=== PERFIL DO BENEFICIÁRIO ===")
    print(f"Público: {perfil['publico_alvo']}")
    print(f"Titulação: {perfil['titulacao_minima']}")

    # Cronograma
    cronograma = analyzer.extrair_cronograma_estruturado(texto_exemplo)
    print(f"\n=== CRONOGRAMA ===")
    print(f"Datas importantes: {cronograma['datas_importantes']}")