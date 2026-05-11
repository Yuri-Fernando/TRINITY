# Regulatory Uncertainty LLM Index

![Architecture](docs/architecture.png)

## Objetivo

Desenvolver um pipeline escalável baseado em LLMs e NLP para extração, classificação e mensuração de sinais de incerteza regulatória a partir de documentos regulatórios, notícias econômicas, comunicados institucionais e textos financeiros em larga escala.

## Motivação

A incerteza regulatória é um fator crítico de risco para mercados financeiros, instituições e formuladores de política. O desafio operacional é monitorar manualmente o volume massivo de documentos, discursos, comunicados e notícias que geram sinais de mudança regulatória em tempo real. 

Este projeto implementa uma abordagem baseada em LLMs para:

- **Capturar sinais** de ambiguidade e mudança regulatória em documentos não-estruturados
- **Quantificar** incerteza através de scoring probabilístico e análise temporal
- **Detectar** drift regulatório e anomalias em séries temporais
- **Escalar** ingestion e processamento através de pipelines distribuídos

## Pipeline de Dados

```
Data Sources (Regulatory Docs, News, Transcripts)
        ↓
    Preprocessing & Semantic Chunking
        ↓
    Embeddings Generation (Sentence Transformers)
        ↓
    Vector Database (FAISS / ChromaDB)
        ↓
    LLM-based Uncertainty Classification
        ↓
    Probabilistic Scoring Engine
        ↓
    Temporal Aggregation & Index Generation
        ↓
    Regulatory Uncertainty Index
        ↓
    Dashboard & Real-time Monitoring
```

## Componentes Principais

### 1. **Ingestion Pipeline** (`src/ingestion/`)
- `web_scraping.py` – Coleta de notícias e documentos públicos
- `regulatory_docs.py` – Parsing de comunicados regulatórios e regulações
- `news_pipeline.py` – Pipeline incremental para feeds de notícias econômicas

### 2. **Preprocessing** (`src/preprocessing/`)
- `cleaning.py` – Normalização e limpeza de texto
- `chunking.py` – Semantic chunking com overlap para context preservation
- `semantic_segmentation.py` – Segmentação de documentos por tópico

### 3. **Embeddings** (`src/embeddings/`)
- `embedding_generator.py` – Geração de embeddings vetoriais de alta dimensão
- `vector_store.py` – Abstração para FAISS/ChromaDB com indexação

### 4. **LLM Layer** (`src/llm/`)
- `uncertainty_classifier.py` – Classificação contextual de incerteza regulatória
- `prompt_templates.py` – Prompts otimizados para extração de sinais
- `semantic_scoring.py` – Scoring baseado em similaridade semântica

### 5. **Modeling** (`src/modeling/`)
- `uncertainty_index.py` – Agregação de scores em índice temporal
- `temporal_analysis.py` – Análise de séries temporais e volatilidade
- `drift_detection.py` – Detecção de anomalias e mudanças estruturais

### 6. **Visualization** (`src/visualization/`)
- `dashboard.py` – Dashboard interativo (Streamlit/FastAPI)

## Stack Tecnológico

| Camada | Tecnologia |
|--------|-----------|
| **LLMs** | OpenAI API / Anthropic Claude |
| **Embeddings** | Sentence Transformers |
| **Vector Store** | FAISS / ChromaDB |
| **Database** | PostgreSQL |
| **API Server** | FastAPI |
| **NLP Pipeline** | LangChain |
| **Data Processing** | Pandas, NumPy |
| **ML/Stats** | Scikit-learn, SciPy |
| **Dashboard** | Streamlit |
| **Container** | Docker |
| **Orchestration** | AWS Lambda / Airflow |

## Features de Impressão

### Pipeline
- ✓ Ingestão automática e escalável
- ✓ Chunking semântico com preservação de contexto
- ✓ Embeddings vetoriais de alta dimensão
- ✓ Classificação contextual de incerteza
- ✓ Scoring temporal e agregação

### IA
- ✓ Semantic retrieval com similaridade vetorial
- ✓ LLM classification zero-shot/few-shot
- ✓ Topic extraction automática
- ✓ Regulatory signal detection
- ✓ Semantic similarity analysis

### Quantitativo
- ✓ Probabilistic scoring com calibração
- ✓ Uncertainty weighting por relevância
- ✓ Drift detection (CUSUM, changepoint analysis)
- ✓ Temporal volatility analysis
- ✓ Index aggregation com pesos Bayesianos

## Validação & Benchmarks

O índice é validado através de:

1. **Event-Based Validation** – Comparação com eventos de mercado conhecidos
2. **Temporal Consistency** – Análise de correlação com índices econômicos (VIX, credit spreads)
3. **Drift Detection** – Monitoramento de estabilidade estatística
4. **Interpretability** – Rastreabilidade de sinais até fontes originais

## Requisitos & Setup

### Dependências
```bash
pip install -r requirements.txt
```

### Variáveis de Ambiente
```bash
export OPENAI_API_KEY="sk-..."
export DATABASE_URL="postgresql://user:password@localhost/regulatory_db"
export VECTOR_STORE_PATH="./data/embeddings/"
```

### Docker
```bash
docker build -t regulatory-uncertainty-index .
docker run -e OPENAI_API_KEY=sk-... regulatory-uncertainty-index
```

## Estrutura de Dados

### Raw Data
- Documentos regulatórios (PDF, HTML)
- Feeds de notícias (JSON)
- Transcrições de discursos (TXT)
- Comunicados institucionais (HTML)

### Processed Data
- Chunks semânticos com metadados
- Embeddings vetoriais (numpy arrays)
- Classification scores (CSV)

### Index Output
- Séries temporais de índice (Parquet)
- Signals e anomalias (JSON)
- Dashboard state (SQLite)

## Uso

### 1. Executar Pipeline Completo
```bash
python src/main.py --mode full --date 2026-05-11
```

### 2. Ingestion Apenas
```bash
python src/ingestion/web_scraping.py --sources reuters,bloomberg,fed
```

### 3. Análise Exploratória
```bash
jupyter notebook notebooks/exploratory_analysis.ipynb
```

### 4. Dashboard
```bash
streamlit run dashboard/app.py
```

## Escalabilidade

O sistema é projetado para:
- **Horizontal scaling** via AWS Lambda para processamento
- **Distributed embeddings** usando batch processing
- **Incremental updates** ao índice (não reprocessar tudo)
- **Real-time monitoring** com streaming pipeline
- **Multi-tenancy** com isolamento de dados

## Licença

MIT

## Contato & Contribuições

Contribuições são bem-vindas. Abra uma issue ou envie um PR com:
- Novos sources de dados
- Melhorias em scoring
- Otimizações de pipeline
- Validações de benchmark
