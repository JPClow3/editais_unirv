# Sistema de Web Scraping de Editais FAPEG

## 📋 Descrição

Sistema automatizado para coleta e extração de informações de editais da FAPEG (Fundação de Amparo à Pesquisa do Estado de Goiás).

## 🔧 Dependências

Instale as bibliotecas necessárias:

```bash
pip install requests beautifulsoup4 PyPDF2
```

## 📁 Estrutura do Projeto

```
projeto/
│
├── fapeg_scraper.py          # Scraper principal
├── fapeg_pdf_extractor.py    # Extrator de PDFs
├── editais_fapeg.json        # Resultado básico
└── editais_completo.json     # Resultado com análise de PDFs
```

## 🚀 Como Usar

### Opção 1: Coleta Básica (sem análise de PDFs)

```python
from core.scraper import FAPEGScraper

# Criar instância do scraper
scraper = FAPEGScraper()

# Coletar editais de 3 páginas
editais = scraper.coletar_todos_editais(max_paginas=3)

# Salvar resultados
scraper.salvar_resultados(editais, 'editais_basico.json')

print(f"Total coletado: {len(editais)} editais")
```

### Opção 2: Coleta Completa (com análise de PDFs)

```python
from core.scraper import FAPEGScraper
from core.pdf_extractor import EditalPDFExtractor

# Coletar lista de editais
scraper = FAPEGScraper()
editais = scraper.coletar_todos_editais(max_paginas=2)

# Processar PDFs
extrator = EditalPDFExtractor()

for edital in editais:
    if edital.get('links_pdf'):
        primeiro_pdf = edital['links_pdf'][0]['url']
        info_pdf = extrator.processar_edital(primeiro_pdf)
        edital['detalhes_pdf'] = info_pdf

# Salvar resultado completo
scraper.salvar_resultados(editais, 'editais_completo.json')
```

### Opção 3: Processar PDF Individual

```python
from core.pdf_extractor import EditalPDFExtractor

extrator = EditalPDFExtractor()

url_pdf = "https://goias.gov.br/fapeg/wp-content/uploads/sites/5/2025/09/Chamada_28_2025.pdf"
info = extrator.processar_edital(url_pdf)

print(f"Valores: {info['valores']}")
print(f"Datas: {info['datas']}")
print(f"Público-alvo: {info['publico_alvo']}")
```

## 📊 Estrutura dos Dados Extraídos

### Informações Básicas

```json
{
  "titulo": "CHAMADA PÚBLICA FAPEG Nº 28/2025",
  "url": "https://goias.gov.br/fapeg/...",
  "numero_edital": "28/2025",
  "data_publicacao": "16 setembro 2025",
  "data_atualizacao": "16 de setembro de 2025",
  "entidade_principal": "FAPEG",
  "area_foco": ["Infraestrutura", "Pesquisa"],
  "tipo_apoio": "Infraestrutura"
}
```

### Informações do PDF

```json
{
  "detalhes_pdf": {
    "valores": {
      "valor_total": 500000.00,
      "valor_por_projeto": 50000.00,
      "quantidade_projetos": 10,
      "contrapartida": "20%"
    },
    "datas": {
      "inscricoes_inicio": "16/09/2025",
      "inscricoes_fim": "30/10/2025",
      "resultado_preliminar": "15/11/2025",
      "resultado_final": "30/11/2025"
    },
    "publico_alvo": ["Pesquisadores", "ICTs"],
    "areas_tematicas": ["Tecnologia", "Saúde", "Inovação"],
    "requisitos": [
      "Ser pesquisador vinculado a ICT goiana",
      "Ter doutorado completo",
      "..."
    ]
  }
}
```

## ⚙️ Configurações Avançadas

### Ajustar Delay Entre Requisições

```python
import time

# No loop de coleta
for edital in editais:
    processar_edital(edital)
    time.sleep(2)  # Aguarda 2 segundos entre requisições
```

### Filtrar por Data

```python
from datetime import datetime

def filtrar_editais_recentes(editais, dias=30):
    hoje = datetime.now()
    editais_recentes = []
    
    for edital in editais:
        # Implementar lógica de filtro por data
        pass
    
    return editais_recentes
```

### Exportar para CSV

```python
import csv
import json

def exportar_csv(arquivo_json, arquivo_csv):
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        editais = json.load(f)
    
    with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'titulo', 'numero_edital', 'data_publicacao',
            'entidade_principal', 'area_foco', 'url'
        ])
        writer.writeheader()
        
        for edital in editais:
            writer.writerow({
                'titulo': edital.get('titulo'),
                'numero_edital': edital.get('numero_edital'),
                'data_publicacao': edital.get('data_publicacao'),
                'entidade_principal': edital.get('entidade_principal'),
                'area_foco': ', '.join(edital.get('area_foco', [])),
                'url': edital.get('url')
            })

exportar_csv('editais_completo.json', 'editais.csv')
```

## 🔍 Funcionalidades Principais

### 1. Identificação Automática de Entidades
- FAPEG
- FINEP
- SEBRAE
- SECTI
- CNPq
- CAPES

### 2. Classificação de Áreas
- Inovação
- Pesquisa
- Infraestrutura
- Mobilidade
- Humanidades
- Energia
- Bolsas

### 3. Extração de Valores
- Valor total do edital
- Valor por projeto
- Quantidade de projetos
- Contrapartida exigida

### 4. Cronograma
- Datas de inscrição
- Resultados preliminares
- Resultado final
- Período de execução

### 5. Público-Alvo
- Pesquisadores
- Estudantes
- Empresas
- ICTs
- ONGs
- Empreendedores

## ⚠️ Considerações Importantes

1. **Respeite o robots.txt** do site
2. **Use delays** entre requisições para não sobrecarregar o servidor
3. **Verifique regularmente** se a estrutura HTML do site mudou
4. **Valide os dados** extraídos antes de usar em produção
5. **PDFs podem ter layouts variados** - a extração pode não ser 100% precisa

## 🐛 Tratamento de Erros

O sistema inclui tratamento de erros para:
- Falhas de conexão
- PDFs corrompidos ou inacessíveis
- Mudanças na estrutura HTML
- Timeouts

## 📈 Melhorias Futuras

- [ ] Cache de resultados para evitar requisições duplicadas
- [ ] Detecção automática de mudanças na estrutura HTML
- [ ] OCR para PDFs escaneados
- [ ] Análise com NLP para melhor extração de requisitos
- [ ] Dashboard web para visualização dos dados
- [ ] Sistema de notificações para novos editais
- [ ] Integração com banco de dados

## 📝 Exemplo de Uso Completo

```python
import json
from core.scraper import FAPEGScraper
from core.pdf_extractor import EditalPDFExtractor


def main():
    # Inicializar
    scraper = FAPEGScraper()
    extrator = EditalPDFExtractor()

    # Coletar editais
    print("Coletando editais...")
    editais = scraper.coletar_todos_editais(max_paginas=5)

    # Processar PDFs
    print("\nProcessando PDFs...")
    for i, edital in enumerate(editais, 1):
        print(f"{i}/{len(editais)}: {edital['titulo']}")

        if edital.get('links_pdf'):
            try:
                primeiro_pdf = edital['links_pdf'][0]['url']
                info_pdf = extrator.processar_edital(primeiro_pdf)
                edital['detalhes_pdf'] = info_pdf
            except Exception as e:
                print(f"  Erro: {e}")

    # Salvar
    scraper.salvar_resultados(editais, 'editais_final.json')

    # Estatísticas
    print("\n=== ESTATÍSTICAS ===")
    print(f"Total de editais: {len(editais)}")

    com_pdf = sum(1 for e in editais if e.get('detalhes_pdf'))
    print(f"PDFs processados: {com_pdf}")

    areas = {}
    for e in editais:
        for area in e.get('area_foco', []):
            areas[area] = areas.get(area, 0) + 1

    print("\nEditais por área:")
    for area, count in sorted(areas.items(), key=lambda x: -x[1]):
        print(f"  {area}: {count}")


if __name__ == "__main__":
    main()
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se todas as dependências estão instaladas
2. Teste com um único edital primeiro
3. Verifique os logs de erro
4. Confirme que o site está acessível

## 📄 Licença

Uso educacional e pessoal. Respeite os termos de uso do site da FAPEG.
