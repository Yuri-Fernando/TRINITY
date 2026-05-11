# Metodologia – Regulatory Uncertainty LLM Index

## 1. Definição de Incerteza Regulatória

Incerteza regulatória é quantificada como a **probabilidade implícita de mudança significativa no ambiente regulatório** que afeta decisões de negócio, alocação de capital ou conformidade operacional.

Indicadores textuais de incerteza:
- **Ambiguidade**: Linguagem vaga ("pode", "poderia", "potencialmente")
- **Condicionalidade**: Declarações condicionais ("se", "desde que", "sob condição")
- **Incompletude**: Orientação pendente ("a ser determinado", "em desenvolvimento")
- **Mudanças de política**: Reversões, emendas ou atualizações de regulações
- **Conflito**: Direcionamentos contraditórios ou múltiplas interpretações
- **Novidade**: Áreas regulatórias emergentes sem precedente

## 2. Pipeline de Dados

### 2.1 Ingestion (Coleta)

**Fontes de dados:**
- Comunicados da **Federal Reserve** (press releases, statements, minutes)
- **SEC Edgar** (10-K, 10-Q, 8-K filings)
- **Feeds de notícias econômicas** (Reuters, Bloomberg, Wall Street Journal)
- **Bancos centrais regionais** (discursos, relatórios)
- **Transcripts de audiências** (Congressional hearings)

**Frequência**: Atualização diária

**Deduplicação**: Hashing MD5 para detectar documentos duplicados

### 2.2 Preprocessing (Limpeza & Chunking)

**Etapas:**
1. **Normalização**: Remoção de metadados, padronização de espaçamento
2. **Chunking semântico**: Divisão respeitando limites de sentença/parágrafo
   - Tamanho alvo: 512 tokens (~2KB)
   - Overlap: 100 caracteres para preservação de contexto
3. **Remoção de boilerplate**: Cabeçalhos, rodapés, disclaimers

**Estratégia de chunking**: Híbrida (respeita sentença dentro do limite de tamanho)

### 2.3 Embeddings (Vetorização)

**Modelo**: Sentence Transformers (`all-MiniLM-L6-v2` ou `all-mpnet-base-v2`)
- Dimensionality: 384 ou 768
- Normalização: L2
- Buscas semânticas: Cosine similarity

**Propósito**:
- Recuperação semântica (RAG)
- Clustering de documentos relacionados
- Análise de similaridade temporal

### 2.4 LLM Classification (Classificação)

**Modelo**: GPT-3.5-turbo ou Claude (via API)

**Tarefa**: Zero-shot classification de incerteza regulatória

**Prompt**:
```
Analise o seguinte texto regulatório para sinais de incerteza regulatória.
Classifique em: NONE, LOW, MODERATE, HIGH, CRITICAL
Forneca: signals, keywords, regulatory_domain, reasoning
```

**Outputs**:
- `uncertainty_level`: Enum [NONE, LOW, MODERATE, HIGH, CRITICAL]
- `score`: Float normalizado [0, 1]
- `confidence`: Confiança do LLM [0, 1]
- `signals`: Lista de indicadores identificados
- `keywords`: Frases-chave de incerteza
- `regulatory_domain`: Domínio (credit, market, operational, etc.)

### 2.5 Index Aggregation (Agregação)

**Estratégia de ponderação**:
```
Index(t) = Σ(score_i × confidence_i × weight_i) / Σ(weight_i)
```

Onde:
- `score_i`: Incerteza normalizada do documento i
- `confidence_i`: Confiança do LLM na classificação
- `weight_i`: Peso temporal = decay_factor^(days_ago / 30)

**Sub-índices por domínio**: Agregação separada para credit, market, operational

### 2.6 Smoothing & Volatility

**Suavização**: Exponential Moving Average (EMA)
```
EMA_t = α × Index_t + (1-α) × EMA_{t-1}
α = 0.3 (default)
```

**Volatilidade**: Rolling standard deviation (janela 30 dias)
```
Volatility_t = std(Index_{t-30:t})
```

## 3. Validação & Benchmarks

### 3.1 Event-Based Validation

Comparação com eventos econômicos conhecidos:
- Mudanças de política do Fed
- Regulações da SEC (Dodd-Frank, etc.)
- Crisis econômicas (correlação com VIX, credit spreads)

**Métrica**: Correlação com índices econômicos conhecidos

### 3.2 Temporal Consistency

- **Autocorrelação**: Persistence do índice (~0.7-0.8 esperado)
- **Reversibilidade**: Comportamento durante períodos de certeza vs. incerteza

### 3.3 Interpretability

- Rastreabilidade de scores até chunks originais
- Extração de top N documentos dirigindo o índice
- Análise de signals mais frequentes

## 4. Componentes Técnicos

### 4.1 Vector Database

**Opções**: FAISS (local) ou ChromaDB (managed)
- Armazenamento: ~384/768 dimensional vectors
- Operações: Similarity search, batch ingest
- Escala: Milhões de chunks

### 4.2 Database (PostgreSQL)

Tabelas:
- `documents`: Metadados dos documentos
- `chunks`: Chunks com texto, embeddings, timestamps
- `classifications`: Scores de incerteza por chunk
- `index_daily`: Valores diários do índice
- `signals`: Sinais detectados por tipo

### 4.3 API (FastAPI)

Endpoints:
- `GET /index/current` – Valor atual do índice
- `GET /index/historical?days=30` – Série histórica
- `POST /search` – Busca semântica
- `GET /signals?domain=credit` – Sinais por domínio
- `POST /classify` – Classificação ad-hoc de texto

### 4.4 Dashboard (Streamlit)

- Série temporal com EMA
- Sub-índices por domínio
- Top documents dirigindo o índice
- Distribution de uncertainty levels
- Volatility chart

## 5. Escalabilidade

### Horizontal Scaling

- **Ingestion**: Parallelização com Airflow/Temporal
- **Embedding**: Batch processing em GPU (AWS Lambda)
- **Classification**: Batch API calls com rate limit handling
- **Storage**: PostgreSQL + FAISS replicado

### Incremental Updates

- Novos documentos processados diretamente (sem reprocessamento total)
- Index update: Apenas add novos scores, recalcular agregado
- Caching de embeddings (não recompute)

### Cost Optimization

- Embeddings cached indefinidamente
- LLM classification com batch & cache (mesma prompt = mesmo resultado)
- Database com TTL para dados históricos

## 6. Validação Empírica

### 6.1 Backtesting

Comparar índice histórico com:
- **VIX**: S&P 500 volatility index
- **TED Spread**: Credit stress indicator
- **Fed Funds Futures**: Market expectations
- **Key rate OAS**: Credit spreads

### 6.2 Sensibility Checks

- Index sobe durante Fed tightening cycles
- Index sobe durante policy uncertainty (eleições, Brexit, etc.)
- Index correlação positiva com regulatory announcements

### 6.3 Qualitative Review

- Manual review de chunks HIGH/CRITICAL
- Confirmação de que sinais são realmente relevantes
- Ajuste de prompts se false positives

## 7. Próximos Passos

1. **Fine-tuning**: Treinar LLM específico para classificação regulatória
2. **Multi-language**: Estender para documentos em português, espanhol, etc.
3. **Causal Analysis**: Identificar quais documentos causam mudanças de índice
4. **Nowcasting**: Prever índice futuro com features econômicas
5. **Attribution**: Explicar variação do índice por factor (policy, market, etc.)

---

## Referências

- Alesina, A., Passalacqua, A. (2016). "The Political Economy of Government Debt"
- Julio, B., Yook, Y. (2012). "Political Uncertainty and Corporate Investment Cycles"
- Ludvigson, S., Ma, S., Ng, S. (2021). "Uncertainty and Business Cycles"
- Bloom, N. (2009). "The Impact of Uncertainty Shocks"
