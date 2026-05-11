# Getting Started – Regulatory Uncertainty LLM Index

## Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd regulatory-uncertainty-llm-index

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-your-api-key-here
DATABASE_URL=postgresql://user:password@localhost/regulatory_db
VECTOR_STORE_PATH=./data/embeddings/
EOF
```

### 3. Run the Pipeline

```bash
# Full pipeline
python src/main.py --mode full

# Specific stage
python src/main.py --mode ingestion
python src/main.py --mode preprocess
python src/main.py --mode embed
python src/main.py --mode classify
python src/main.py --mode index
```

### 4. Explore Data

```bash
# Run exploratory analysis
jupyter notebook notebooks/exploratory_analysis.ipynb

# Start dashboard
streamlit run dashboard/app.py
```

## Project Structure

```
regulatory-uncertainty-llm-index/
├── src/
│   ├── ingestion/           # Data collection
│   ├── preprocessing/       # Text cleaning & chunking
│   ├── embeddings/          # Vector generation
│   ├── llm/                 # LLM classification
│   ├── modeling/            # Index aggregation
│   └── visualization/       # Dashboard components
│
├── data/
│   ├── raw/                 # Raw documents
│   ├── processed/           # Processed chunks & scores
│   └── embeddings/          # Vector embeddings
│
├── notebooks/               # Jupyter analysis notebooks
├── dashboard/               # Streamlit dashboard
├── docs/                    # Documentation
│
├── requirements.txt         # Python dependencies
├── config.yaml              # Configuration
├── Dockerfile               # Container image
└── README.md                # Project overview
```

## Core Modules

### 1. Ingestion (`src/ingestion/`)
- **RegulatoryDocumentScraper**: Scrapes Fed, SEC, news
- Supports parallel data collection
- Built-in deduplication

### 2. Preprocessing (`src/preprocessing/`)
- **SemanticChunker**: Intelligent text splitting
- Preserves context with overlap
- Three strategies: sentence, paragraph, hybrid

### 3. Embeddings (`src/embeddings/`)
- **EmbeddingGenerator**: Sentence Transformers wrapper
- Semantic search capabilities
- Optional caching to disk

### 4. LLM Classification (`src/llm/`)
- **UncertaintyClassifier**: Zero-shot uncertainty detection
- Extracts signals, keywords, domains
- Configurable confidence threshold

### 5. Indexing (`src/modeling/`)
- **UncertaintyIndex**: Temporal aggregation
- Probability-weighted scoring
- Rolling index with EMA smoothing

## Configuration

Edit `config.yaml` to customize:
- Data sources and update frequency
- Model selection (embedding, LLM)
- Index parameters (smoothing, decay)
- Database connection
- API server settings

## Development Workflow

### Adding a New Data Source

1. Create scraper in `src/ingestion/`
2. Inherit from base scraper class
3. Implement `scrape()` and `parse()` methods
4. Add to main pipeline in `src/main.py`

### Custom Uncertainty Metrics

1. Extend `UncertaintyClassifier` in `src/llm/`
2. Override `classify()` method
3. Return custom `UncertaintyScore`

### API Integration

1. Endpoints defined in `src/visualization/api.py`
2. Uses FastAPI with async support
3. Integrates with PostgreSQL + FAISS

## Deployment

### Local Development
```bash
docker build -t regulatory-uncertainty-index .
docker run -e OPENAI_API_KEY=sk-... regulatory-uncertainty-index
```

### AWS Lambda (Serverless)
```bash
# Package for Lambda
pip install -r requirements-lambda.txt -t package/
cd package && zip -r ../function.zip . && cd ..
zip function.zip -r src/ && zip function.zip config.yaml

# Deploy to AWS
aws lambda create-function \
  --function-name regulatory-uncertainty \
  --runtime python3.10 \
  --zip-file fileb://function.zip
```

### Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
kubectl port-forward svc/regulatory-uncertainty 8000:8000
```

## Troubleshooting

### OpenAI API Key Issues
```python
import os
os.getenv('OPENAI_API_KEY')  # Should print your key
```

### FAISS Index Too Large
- Use ChromaDB instead (auto-managed)
- Or implement index sharding

### LLM Rate Limits
- Add exponential backoff in `uncertainty_classifier.py`
- Use batch API for high volume

### Database Connection Errors
```bash
# Test PostgreSQL connection
psql postgresql://user:password@localhost/regulatory_db
```

## Next Steps

1. **Extend data sources**: Add more regulatory sources
2. **Fine-tune classifier**: Train domain-specific uncertainty model
3. **Add validation**: Compare with economic indicators (VIX, spreads)
4. **Real-time monitoring**: Deploy API for live queries
5. **Multi-language**: Support Portuguese, Spanish documents

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Federal Reserve Open Data](https://www.federalreserve.gov/datadownload/)
- [SEC EDGAR API](https://www.sec.gov/edgar/)

## Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request
4. Include tests & documentation

## License

MIT

## Contact

Yuri Dubberstein – yuri.dubbern@gmail.com

---

**Built with research engineering patterns for scalable, production-ready AI systems.**
