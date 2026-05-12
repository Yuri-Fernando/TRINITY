# O Que Este Projeto Faz - Explicação Completa

## Resumo em 1 Linha
**Monitora e quantifica incerteza regulatória em tempo real usando IA, transformando documentos regulatórios em um índice numérico.**

---

## O Problema Real

Imagine você trabalha em um **banco, seguadora ou fundo de investimento**.

Todos os dias:
- A **Federal Reserve** publica comunicados
- A **SEC** divulga regulações novas
- **Notícias econômicas** mencionam mudanças nas regras
- **Discursos de políticos** sinalizam possíveis mudanças

**Problema:** São **centenas de documentos por dia**. Ninguém consegue ler tudo manualmente. E você precisa saber:
- Qual é o nível de incerteza regulatória AGORA?
- Está aumentando ou diminuindo?
- Qual área está mais incerta (crédito, mercado, operações)?
- Há picos de incerteza que sinalizam risco iminente?

---

## A Solução: Um Pipeline Automático

Este projeto cria um **sistema de IA que:**

1. **Coleta** documentos regulatórios automaticamente
2. **Processa** com semântica profunda (embeddings vetoriais)
3. **Classifica** o nível de incerteza com LLMs
4. **Agrega** em um índice temporal
5. **Monitora** padrões e anomalias em tempo real

---

## As 5 Etapas do Pipeline

### 1️⃣ **INGESTION (Coleta)**
```
Federal Reserve (statements, press releases)
       ↓
SEC Edgar (10-K, 10-Q, 8-K filings)
       ↓
Notícias econômicas (Reuters, Bloomberg)
       ↓
Documentos brutos em data/raw/
```

**Exemplo:** "The Federal Reserve issued new guidance on credit risk management."

---

### 2️⃣ **PREPROCESSING (Limpeza & Chunking)**
Um documento tem 50 páginas, não cabe na memória de uma vez.

**Solução:** Divide em pedaços inteligentes (~512 tokens / ~2KB) mas **respeitando sentença**:

```
Documento Original:
"The Federal Reserve issued new guidance on credit risk... 
Banks are required to implement enhanced monitoring frameworks..."

↓ Chunking Semântico

Chunk 1: "The Federal Reserve issued new guidance..." (512 tokens)
  [OVERLAP de 100 caracteres para contexto]
Chunk 2: "...monitoring frameworks. The guidance may be..." (512 tokens)
```

**Resultado:** 1 documento → múltiplos chunks processáveis

---

### 3️⃣ **EMBEDDINGS (Vetorização)**
Converte **texto em números** (vetores) que máquinas entendem:

```
Texto: "The Federal Reserve may change policy"
         ↓
Vetor: [0.234, -0.891, 0.456, ..., 0.123]  (384 dimensões)
```

**Por que?**
- Permite buscar documentos **semanticamente similares**
- "Fed changes" é similar a "regulatory shifts"
- Máquina entende o significado, não só palavras

---

### 4️⃣ **LLM CLASSIFICATION (Classificação com IA)**
Usa GPT-3.5 ou Claude para perguntar:

> "Este texto mostra **INCERTEZA regulatória**?"

**O que o LLM detecta:**
- ✓ Linguagem ambígua ("pode", "poderia", "potencialmente")
- ✓ Condicionalidade ("se", "desde que", "provided that")
- ✓ Incompletude ("a ser determinado", "TBD", "pending")
- ✓ Mudanças de política (reversões, emendas)
- ✓ Conflitos de direcionamento
- ✓ Novos tópicos regulatórios emergentes

**Exemplo:**
```json
Texto: "The Fed may implement new policies, pending final review"

LLM Output:
{
  "uncertainty_level": "HIGH",
  "score": 0.74,
  "confidence": 0.89,
  "signals": [
    "ambiguous_language",
    "pending_decision"
  ],
  "regulatory_domain": "credit"
}
```

---

### 5️⃣ **INDEX GENERATION (Agregação Temporal)**
Combina **1000 scores individuais** em **1 índice único** que muda ao longo do tempo.

**Fórmula:**
```
Index(t) = Σ(score × confidence × peso_temporal) / Σ(pesos)
```

Onde:
- `score` = incerteza [0-1]
- `confidence` = confiança do LLM [0-1]
- `peso_temporal` = documentos recentes têm peso maior

**Features:**
- Sub-índices por domínio (credit=0.72, market=0.45, operational=0.38)
- Smoothing com EMA (reduz ruído)
- Volatility tracking (picos indicam risco)
- Anomaly detection (3σ acima da média)

---

## Saídas: O Que Você Vê

### 📊 Arquivo CSV: `index_pipeline.csv`
```csv
date,index_value,volatility,smoothed_index,signal_count,document_count
2026-05-01,0.452,0.087,0.445,3,15
2026-05-02,0.468,0.092,0.456,5,18
2026-05-03,0.441,0.078,0.450,2,12
```

**Interpretação:**
- **2026-05-01:** Incerteza = 0.452 (MODERATE) | 3 eventos HIGH | 15 docs analisados
- **2026-05-02:** Incerteza subiu para 0.468 | 5 eventos HIGH | Algo anormal aconteceu!

### 📈 Dashboard Streamlit
Visualiza tudo interativamente:
```
┌─────────────────────────────────────┐
│ Current Index: 0.452 ↑ 0.016        │
│ Mean: 0.445 | Peak: 0.468           │
└─────────────────────────────────────┘
     [Gráfico da série temporal]
     [Distribuição de scores]
     [Breakdown por domínio]
     [Top 10 eventos HIGH]
```

---

## Casos de Uso Reais

### 1. **Risk Management**
```
Pergunta: "Qual é a incerteza regulatória AGORA?"
Resposta: Índice = 0.68 → MODERATE/HIGH
Ação: Aumentar provisões de compliance, preparar scenario analysis
```

### 2. **Trading / Markets**
```
Pergunta: "Picos de incerteza regulatória = volatilidade de mercado?"
Resposta: Correlação com VIX = 0.72 (forte!)
Ação: Usar índice como preditor de volatilidade
```

### 3. **Policy Monitoring**
```
Pergunta: "Qual domínio está mais incerto?"
Resposta: 
  - Credit:       0.72 (HIGH)
  - Market:       0.45 (MODERATE)
  - Operational:  0.38 (LOW)
Ação: Focar recursos em credit risk management
```

### 4. **Early Warning System**
```
Pergunta: "Há anomalias?"
Resposta: Índice 3σ acima da média → ALERT!
Ação: Investigar qual documento/assunto causou o pico
```

---

## Stack Técnico (O Que Usa)

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Coleta** | Web scraping + APIs | Pega documentos |
| **NLP** | LangChain | Orquestra pipeline |
| **Embeddings** | Sentence Transformers | Vetoriza texto |
| **LLM** | GPT-3.5 / Claude | Classifica incerteza |
| **Index** | Pandas + NumPy | Agrega dados |
| **Storage** | CSV + FAISS | Persiste tudo |
| **Dashboard** | Streamlit | Visualiza |
| **Deploy** | Docker + AWS | Roda 24/7 |

---

## Diferencial Técnico

**Não é um sentiment analyzer genérico** ("positivo/negativo").

**É específico para INCERTEZA regulatória:**
- Detecta ambiguidade ("pode", "talvez")
- Não detecta só negatividade, mas INCERTEZA
- Entende contexto regulatório
- Permite alertar sobre mudanças eminentes

---

## O Dia a Dia

**Segunda de manhã, você abre o dashboard:**

```
Index: 0.48 (estava 0.42 na sexta)
↑ Subiu 14% em 3 dias → Algo importante aconteceu

Top Events (HIGH uncertainty):
1. "Fed may implement new capital requirements" (0.89)
2. "SEC pending new enforcement guidelines" (0.87)
3. "Credit market regulation subject to change" (0.85)

Domain breakdown:
- Credit: 0.68 ↑↑ (novo risco)
- Operational: 0.42
- Market: 0.38

Ação: Reunião com compliance → Preparar cenários
```

---

## Fluxo Visual Completo

```
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: INGESTION                                      │
│ Fed Statements + SEC + News → data/raw/                │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: PREPROCESSING                                  │
│ Semantic Chunking (512 tokens) + Overlap                │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: EMBEDDINGS                                     │
│ Sentence Transformers → 384-dim vectors                 │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 4: CLASSIFICATION                                 │
│ LLM → Score [0-1] + Confidence + Signals                │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 5: INDEX GENERATION                               │
│ Weighted Aggregation → Daily Index + Volatility         │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ OUTPUT                                                  │
│ Dashboard + CSV + Alerts                                │
└─────────────────────────────────────────────────────────┘
```

---

## Por Que é Importante?

**Antes:** Monitorar manualmente → Lê 50 docs/dia → Perde sinais

**Depois:** Sistema automático → Analisa 500 docs/dia → Nenhum sinal é perdido

**Impacto:**
- ✓ Detecta riscos **mais cedo**
- ✓ Reduz surpresas regulatórias
- ✓ Melhora alocação de recursos
- ✓ Suporta decisões com dados

---

## Em Uma Frase

**"Um sistema de IA que lê centenas de documentos regulatórios por dia, detecta sinais de incerteza e avisa você em tempo real através de um índice numérico."** 📊🚀

---

## Próximos Passos

1. **Rodar:** `python generate_demo_data.py`
2. **Visualizar:** `streamlit run dashboard/app.py`
3. **Experimentar:** Analise os dados em `data/processed/`
4. **Integrar:** Conectar a dados reais (Fed, SEC APIs)
5. **Estender:** Fine-tune LLM para seu domínio

---

**Built as a research engineering prototype for production-grade AI systems.**
