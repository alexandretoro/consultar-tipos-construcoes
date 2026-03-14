# 🏗️ consultar-tipos-construcoes — Busca de Construções por Cidade no Upland

Ferramenta desenvolvida em Python para localizar propriedades com tipos específicos de construção no [Upland](https://upland.me), plataforma de metaverso baseada em blockchain. Permite buscar em uma cidade específica ou em todas as cidades simultaneamente.

---

## 📌 Sobre o Projeto

A ferramenta utiliza boundaries geográficos salvos por bairro para consultar a API de desenvolvedores do Upland, identificar construções do tipo desejado e detalhar o status de venda de cada propriedade encontrada — gerando uma planilha Excel com os resultados ordenados por preço.

---

## ⚙️ Funcionalidades

- **Busca configurável por tipo de construção** — defina um ou mais tipos no arquivo de configuração (ex: `"High-Rise Residential Tower"`, `"Large Factory I"`)
- **Cobertura geográfica ampla** — busca bairro a bairro usando boundaries salvos, cobrindo ~50 cidades ao redor do mundo
- **Dois modos de busca:**
  - `SEARCH_ALL_CITIES = True` — varre todas as cidades disponíveis
  - `SEARCH_ALL_CITIES = False` — busca apenas nas cidades especificadas
- **Filtro de disponibilidade** — opção para exibir apenas propriedades à venda (`ONLY_FOR_SALE`)
- **Consulta a dois endpoints** — combina API pública (status e preço de venda) com API de desenvolvedores autenticada (mint price)
- **Suporte a vendas em UPX e USD** — converte USD para equivalente em UPX automaticamente
- **Geração de planilha Excel** com as seguintes informações por propriedade:
  - ID da propriedade
  - Endereço completo
  - Cidade e bairro
  - Tipo de construção
  - Status (`for sale`, `owner`)
  - Moeda de venda (UPX ou USD)
  - Preço de venda
  - Mint price (UPX)
  - Nome do proprietário
  - Link direto para a propriedade no jogo
- **Resultados ordenados por preço de venda** (menor para maior)
- **Rate limiting e retry automático** — controle de requisições para evitar bloqueios pela API

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| Python | Linguagem principal |
| Requests | Consulta às APIs pública e de desenvolvedores do Upland |
| pandas / openpyxl | Geração e formatação da planilha Excel |
| base64 | Geração do token de autenticação Basic Auth |
| pathlib | Navegação e leitura dos arquivos de boundaries |

---

## 📁 Estrutura do Projeto

```
consultar-tipos-construcoes/
├── buscar_tipos_construcoes.py     # Script principal
├── salvar_boundaries.py            # Script para salvar boundaries das cidades
├── token_autenticacao.py           # Credenciais de autenticação (placeholder)
├── debugar_preco.py                # Utilitário de debug de preços
├── cities_data.json                # Dados das cidades disponíveis
├── boundaries_cidades/             # Boundaries geográficos por cidade (~50 cidades)
│   ├── boundaries_sao_paulo.json
│   ├── boundaries_new_york.json
│   └── ...
└── requirements.txt                # Dependências do projeto
```

> ⚠️ O arquivo `token_autenticacao.py` está incluído no repositório com um placeholder no lugar das credenciais. Substitua `"meu token de autenticação aqui"` pelo seu token de acesso do Upland antes de executar.

---

## ⚙️ Configuração

Antes de executar, ajuste as configurações no topo do arquivo `buscar_tipos_construcoes.py`:

```python
# Tipos de construção para buscar
BUILDING_TYPES = [
    "High-Rise Residential Tower",
    # "Large Factory I",
    # "Natural History Museum I"
]

# Apenas propriedades à venda?
ONLY_FOR_SALE = False  # False = mostra TODAS

# Buscar em todas as cidades ou cidades específicas?
SEARCH_ALL_CITIES = True  # False = usa SPECIFIC_CITIES

SPECIFIC_CITIES = [
    "Sao Paulo"
]
```

---

## 🚀 Como Executar

**Pré-requisitos:**
- Python 3.x
- Credenciais de autenticação do Upland (APP_ID + SECRET_KEY)
- Compatível com Linux e Windows

**Instalação:**

```bash
pip install -r requirements.txt
```

**Passo 1 — Salvar boundaries das cidades (necessário apenas na primeira vez):**

```bash
python salvar_boundaries.py
```

**Passo 2 — Executar a busca:**

```bash
python buscar_tipos_construcoes.py
```

A planilha será gerada automaticamente na pasta do projeto com o timestamp da execução (ex: `construcoes_encontradas_20260222_221448.xlsx`).

---

## 📈 Exemplo de Saída

O repositório inclui a planilha **`construcoes_encontradas_20260222_221448.xlsx`** como exemplo real de saída gerada pela ferramenta.

---

## 💡 Caso de Uso

Ideal para identificar oportunidades de compra de propriedades com construções específicas e raras no mercado secundário do Upland, permitindo:

- Localizar rapidamente propriedades com o tipo de construção desejado em qualquer cidade
- Comparar preços de venda entre propriedades similares
- Identificar propriedades com construções valiosas que ainda não estão à venda

---

## 🤝 Desenvolvimento

Projeto desenvolvido de forma autônoma, com auxílio de ferramentas de Inteligência Artificial (Claude — Anthropic) como suporte ao desenvolvimento. Todas as decisões de arquitetura, configuração, testes e manutenção foram conduzidas pelo autor.

---

*Autor: Alexandre Toro Batista — São Paulo, SP*
*Iniciado em 2026*
