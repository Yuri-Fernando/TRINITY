# Regulatory Uncertainty LLM Index – Project Overview

## O Que Este Projeto Faz?

Este projeto **monitora e quantifica incerteza regulatória em tempo real** usando inteligência artificial.

Imagina que você trabalha com finanças/compliance e precisa saber:
- Quando há mudanças regulatórias em discussão?
- Quão incertas são as novas regras?
- Qual domínio está mais incerto (crédito, mercado, operações)?
- Há um padrão temporal de incerteza crescendo ou caindo?

**Este sistema automatiza essa análise.**

---

## Problema que Resolve

### Desafio Operacional
- Reguladores publicam **centenas de documentos por dia** (Fed, SEC, OCC, FDIC)
- Notícias econômicas mencionam **mudanças regulatórias em tempo real**
- **Monitorar manualmente é impossível** – humanos não conseguem ler tudo

### Solução
Um **pipeline de IA que:**
1. Coleta documentos regulatórios automaticamente
2. Extrai sinais de ambiguidade e incerteza
3. Quantifica incerteza com scores numéricos
4. Agrega em índices temporais
5. Monitora padrões e anomalias

---

## O Pipeline Completo (5 Etapas)

### Etapa 1: INGESTION (Coleta)
**Coleta dados de múltiplas fontes:**
- Comunicados da Federal Reserve
- Filings SEC (10-K, 10-Q, 8-K)
- Feeds de notícias econômicas
- Transcripts de discursos

**Arquivo:** `src/ingestion/regulatory_docs.py`

**O que faz:**
```python
scraper = RegulatoryDocumentScraper()
docs = scraper.scrape_fed_statements(limit=20)  # Pega 20 últimos
```

**Output:** Documentos brutos (HTML, PDF, texto)

---

### Etapa 2: PREPROCESSING (Limpeza & Chunking)
**Divide documentos grandes em pedaços inteligentes:**

Problema: Um documento tem 50 páginas, não cabe em memory de uma vez.

Solução: Divide em **chunks semânticos** de ~512 tokens (~2KB) com **overlap de 100 chars** para preservar contexto.

**Arquivo:** `src/preprocessing/chunking.py`

**Exemplo:**
```
Documento: "The Federal Reserve issued new guidance on credit risk..."
            [CHUNK 1 - 512 tokens]
                      [OVERLAP - 100 chars]
                                    [CHUNK 2 - 512 tokens]
                                              [OVERLAP]
                                                       [CHUNK 3...]
```

**Output:** N chunks com metadados (posição, tamanho, tokens)

---

### Etapa 3: EMBEDDINGS (Vetorização)
**Converte texto em números (vetores) que computadores entendem:**

Um texto "The Federal Reserve may change policy" vira um vetor de 384 números que representa seu **significado semântico**.

**Arquivo:** `src/embeddings/embedding_generator.py`

**Técnica:** Sentence Transformers (modelo pré-treinado)

**Output:** 
```
Chunk: "The Fed may implement new rules pending final review"
Vector: [0.234, -0.891, 0.456, ..., 0.123]  (384 dimensões)
```

**Benefício:** Permite buscar documentos **semanticamente similares** ("Fed changes" ≈ "regulatory shifts")

---

### Etapa 4: LLM CLASSIFICATION (Classificação com IA)
**Usa GPT-3.5 ou Claude para classificar INCERTEZA regulatória.**

Pergunta ao LLM:
> "Este texto mostra sinais de INCERTEZA regulatória? (NONE, LOW, MODERATE, HIGH, CRITICAL)"

**Arquivo:** `src/llm/uncertainty_classifier.py`

**O que o LLM detecta:**
- ✓ Linguagem ambígua ("pode", "poderia", "potencialmente")
- ✓ Condicionalidade ("se", "desde que")
- ✓ Incompletude ("a ser determinado", "em desenvolvimento")
- ✓ Mudanças de política (reversões, emendas)
- ✓ Conflitos de direcionamento

**Output:**
```json
{
  "chunk_id": "doc_001_chunk_5",
  "uncertainty_level": "HIGH",
  "score": 0.74,
  "confidence": 0.89,
  "signals": ["ambiguous_language", "conditional_statements"],
  "keywords": ["may", "pending", "to be determined"],
  "regulatory_domain": "credit"
}
```

---

### Etapa 5: INDEX GENERATION (Agregação Temporal)
**Combina scores individuais em um ÍNDICE único ao longo do tempo.**

Problema: 1000 chunks = 1000 scores. Como virar UM índice?

Solução: **Média ponderada**
```
Index(t) = Σ(score × confidence × peso_temporal) / Σ(pesos)

Onde:
- score = incerteza [0-1]
- confidence = confiança do LLM [0-1]
- peso_temporal = documentos recentes têm peso maior
```

**Arquivo:** `src/modeling/uncertainty_index.py`

**Features:**
- ✓ Sub-índices por domínio (credit, market, operational)
- ✓ Exponential Moving Average (EMA) para suavização
- ✓ Rolling volatility (detecta picos)
- ✓ Detecção de anomalias

**Output:**
```csv
date,index_value,volatility,smoothed_index,signal_count
2026-05-01,0.452,0.087,0.445,3
2026-05-02,0.468,0.092,0.456,5
2026-05-03,0.441,0.078,0.450,2
```

---

## O Que o Notebook Executa

Quando você roda `notebooks/exploratory_analysis.ipynb`, ele executa **todo esse pipeline**:

```
Cell 1-2:   Setup & imports
Cell 3:     Ingestion → Carrega Fed statements
Cell 4:     Preprocessing → Divide em chunks
Cell 5:     Embeddings → Gera vetores
Cell 6:     Classification → Classifica incerteza (mock ou real com API)
Cell 7:     Index → Agrega em índice temporal
Cell 8:     Distribution Analysis → 4 gráficos
Cell 9:     Temporal Analysis → Série temporal
Cell 10:    Domain Analysis → Breakdown por domínio
Cell 11:    Top Events → Eventos de alta incerteza
Cell 12:    Validation → Qualidade dos dados
Cell 13:    Export → Salva CSVs & PNGs
```

---

## Saídas Geradas

### Dados (CSVs)
- `data/processed/index_pipeline.csv` – **Índice diário** (principal output)
- `data/processed/scores_pipeline.csv` – Scores brutos de cada chunk
- `data/embeddings/embeddings.json` – Cache de vetores

### Visualizações (PNGs)
- `distributions.png` – Histogramas de scores
- `temporal_index.png` – Série temporal do índice + EMA
- `domain_analysis.png` – Breakdown por credit/market/operational
- `high_uncertainty_by_domain.png` – Eventos de alta incerteza

### Console Output
```
Score statistics:
  Mean: 0.45
  Std Dev: 0.18
  Min: 0.12
  Max: 0.89

Index Statistics:
  Mean: 0.452
  Std Dev: 0.0234
  Autocorrelation (lag=1): 0.78  ← Indica persistência (bom!)
  
✓ All validation checks passed!
```

---

## Casos de Uso

### 1. Risk Management
"Qual é a incerteza regulatória atual em operações?"
→ Lê o índice atual: 0.68 = **MODERATE**
→ Decisão: Aumentar provisões de compliance

### 2. Trading / Markets
"Há picos de incerteza antes de movimentos de mercado?"
→ Compara índice com volatilidade do VIX
→ Decision: Usar índice como preditor

### 3. Policy Monitoring
"Quais domínios estão mais incertos?"
→ Credit: 0.72 (HIGH)
→ Market: 0.45 (MODERATE)
→ Operational: 0.38 (LOW)
→ Decision: Focar em credit risk management

### 4. Early Warning
"Há anomalias de incerteza?"
→ Detecta mudanças estruturais (CUSUM analysis)
→ Alert: "Incerteza 3σ acima da média"
→ Decision: Investigar causa

---

## Diferencial Técnico

Este **não é um sentiment analyzer simples** (que só detecta positivo/negativo).

**Detecta especificamente INCERTEZA regulatória:**
- Ambiguidade ("pode", "poderia")
- Condicionalidade ("se", "desde que")
- Incompletude ("TBD", "pending")
- Mudanças de política
- Emergência de novos tópicos

Isso é **específico para risco regulatório**, não genérico.

---

## Stack Técnico (o que está dentro)

| Componente | Tecnologia |
|-----------|-----------|
| Coleta | Web scraping + APIs |
| Processamento | LangChain, NLTK, spaCy |
| Embeddings | Sentence Transformers (MiniLM) |
| LLM | GPT-3.5-turbo ou Claude |
| Índices | Numpy, Pandas, SciPy |
| Storage | PostgreSQL, FAISS |
| API | FastAPI |
| Dashboard | Streamlit |
| Infraestrutura | Docker, AWS Lambda |

---

## Próximos Passos (Roadmap)

### Curto Prazo
1. Integrar dados reais (Fed, SEC APIs)
2. Fine-tune LLM para domínio regulatório
3. Validar contra VIX, credit spreads

### Médio Prazo
1. Deploy em produção (AWS Lambda + RDS)
2. API REST para queries em tempo real
3. Dashboard web com Streamlit

### Longo Prazo
1. Nowcasting: prever índice com features econômicas
2. Causal analysis: quais documentos movem o índice?
3. Multi-language: suportar português, espanhol
4. Integração com trading systems

---

## Como Usar na Prática

### Para Pesquisadores
```bash
jupyter notebook notebooks/exploratory_analysis.ipynb
# Analisa dados, gera gráficos, valida pipeline
```

### Para Engenheiros
```bash
python src/main.py --mode full --date 2026-05-11
# Roda pipeline completo para uma data
```

### Para Operações
```bash
docker build -t regulatory-uncertainty-index .
docker run -e OPENAI_API_KEY=sk-... regulatory-uncertainty-index
# Deploy em produção
```

---

## Métricas de Sucesso

- ✓ **Precision**: 85%+ (quanto dos "HIGH" classificados é realmente incerteza)
- ✓ **Recall**: 70%+ (quanto da incerteza real é capturada)
- ✓ **Correlation com VIX**: 0.6+ (índice move junto com volatilidade)
- ✓ **Latência**: <5 min (novos documentos aparecem no índice)
- ✓ **Uptime**: 99.9% (disponível 24/7)

---

## Conclusão

Este projeto **automatiza detecção de incerteza regulatória** usando um pipeline moderno de IA:

1. Coleta documentos regulatórios em escala
2. Processa com semântica profunda (embeddings)
3. Classifica incerteza com LLMs
4. Agrega em índices temporais
5. Monitora padrões e anomalias

Resultado: Um **índice de incerteza regulatória em tempo real** para risk management, trading e policy monitoring.

---

**Construído como research engineering prototype com padrões de produção.**
