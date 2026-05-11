"""
Main pipeline orchestration for Regulatory Uncertainty LLM Index.

Coordinates data ingestion, preprocessing, classification, and index generation.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

# Configure logging
logger.add(sys.stderr, level="INFO")
logger.add("logs/pipeline.log", level="DEBUG", rotation="500 MB")

from ingestion.regulatory_docs import RegulatoryDocumentScraper
from preprocessing.chunking import ChunkingPipeline
from embeddings.embedding_generator import EmbeddingGenerator
from llm.uncertainty_classifier import ClassificationPipeline
from modeling.uncertainty_index import IndexingPipeline


class RegulatoryUncertaintyPipeline:
    """End-to-end pipeline orchestration."""

    def __init__(self, config: dict = None):
        """
        Initialize pipeline.

        Args:
            config: Configuration dictionary with pipeline parameters
        """
        self.config = config or self._default_config()
        self.timestamp = datetime.now().isoformat()

        logger.info(f"Initialized RegulatoryUncertaintyPipeline")
        logger.debug(f"Configuration: {self.config}")

    @staticmethod
    def _default_config() -> dict:
        """Return default configuration."""
        return {
            "data_dir": "./data/",
            "chunk_size": 512,
            "chunk_overlap": 100,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": "gpt-3.5-turbo",
            "smoothing_window": 7,
            "scrape_fed": True,
            "scrape_news": True
        }

    def run(self, mode: str = "full") -> None:
        """
        Run the pipeline.

        Args:
            mode: "full" (all steps) or specific stage
        """
        logger.info(f"Starting pipeline in {mode} mode")

        if mode in ["full", "ingest"]:
            self._stage_ingest()

        if mode in ["full", "preprocess"]:
            self._stage_preprocess()

        if mode in ["full", "embed"]:
            self._stage_embed()

        if mode in ["full", "classify"]:
            self._stage_classify()

        if mode in ["full", "index"]:
            self._stage_index()

        logger.info("Pipeline execution completed")

    def _stage_ingest(self) -> None:
        """Ingest data from regulatory sources."""
        logger.info("=== STAGE 1: DATA INGESTION ===")

        scraper = RegulatoryDocumentScraper(
            cache_dir=os.path.join(self.config["data_dir"], "raw/")
        )

        # Scrape Federal Reserve statements
        if self.config.get("scrape_fed"):
            logger.info("Scraping Federal Reserve statements...")
            fed_docs = scraper.scrape_fed_statements(limit=10)
            scraper.save_documents(fed_docs)
            logger.info(f"Ingested {len(fed_docs)} Fed documents")

        # Load cached documents
        documents = scraper.load_documents_from_cache()
        logger.info(f"Total documents available: {len(documents)}")

    def _stage_preprocess(self) -> None:
        """Preprocess documents into chunks."""
        logger.info("=== STAGE 2: PREPROCESSING ===")

        chunking_pipeline = ChunkingPipeline(
            chunk_size=self.config["chunk_size"],
            overlap=self.config["chunk_overlap"]
        )

        # Create dummy documents for demo
        sample_docs = [
            {
                "id": "doc_001",
                "content": """
                The Federal Reserve announced new regulatory guidance for credit risk management.
                Banks are required to implement enhanced monitoring frameworks. The guidance may be
                subject to further amendments pending stakeholder feedback. Implementation timeline
                to be determined.
                """
            },
            {
                "id": "doc_002",
                "content": """
                Economic uncertainty remains elevated. Market participants face challenges from
                potential policy changes. The situation could evolve significantly depending on
                upcoming decisions by regulatory authorities.
                """
            }
        ]

        chunks = chunking_pipeline.process_documents(sample_docs)
        logger.info(f"Created {len(chunks)} chunks from {len(sample_docs)} documents")

    def _stage_embed(self) -> None:
        """Generate embeddings for chunks."""
        logger.info("=== STAGE 3: EMBEDDINGS ===")

        generator = EmbeddingGenerator(
            model_name=self.config["embedding_model"],
            device="cpu"
        )

        # Sample chunks for demo
        sample_chunks = [
            {
                "id": "chunk_001",
                "text": "The Federal Reserve issued new guidance on credit risk management."
            },
            {
                "id": "chunk_002",
                "text": "Banks must implement enhanced monitoring frameworks for risk assessment."
            }
        ]

        embeddings = generator.encode_chunks_with_ids(sample_chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")

    def _stage_classify(self) -> None:
        """Classify uncertainty in chunks."""
        logger.info("=== STAGE 4: UNCERTAINTY CLASSIFICATION ===")

        try:
            pipeline = ClassificationPipeline(model_name=self.config["llm_model"])

            sample_chunks = [
                {
                    "id": "chunk_001",
                    "text": "The Federal Reserve may implement new policies, pending further analysis."
                },
                {
                    "id": "chunk_002",
                    "text": "Regulatory requirements are clear and implementation is mandatory."
                }
            ]

            scores = pipeline.process_chunks(sample_chunks)
            logger.info(f"Classified {len(scores)} chunks")

            # Export scores
            output_dir = os.path.join(self.config["data_dir"], "processed/")
            os.makedirs(output_dir, exist_ok=True)

            pipeline.export_scores(scores, os.path.join(output_dir, "scores.json"))

        except Exception as e:
            logger.warning(f"Classification stage skipped: {e}")
            logger.info("Using mock data for demo purposes")

    def _stage_index(self) -> None:
        """Generate uncertainty index."""
        logger.info("=== STAGE 5: INDEX GENERATION ===")

        indexing_pipeline = IndexingPipeline(
            smoothing_window=self.config["smoothing_window"]
        )

        # Create sample scores dataframe
        from datetime import datetime, timedelta
        import numpy as np

        sample_scores = [
            {
                "timestamp": datetime.now() - timedelta(days=i),
                "score": 0.4 + 0.15 * np.sin(i / 5),
                "confidence": 0.85,
                "uncertainty_level": "MODERATE" if i % 2 == 0 else "LOW",
                "regulatory_domain": "credit" if i % 2 == 0 else "market"
            }
            for i in range(30)
        ]

        overall_index, rolling_index = indexing_pipeline.process_scores(sample_scores)
        logger.info(f"Overall index value: {overall_index:.4f}")

        # Export
        output_dir = os.path.join(self.config["data_dir"], "processed/")
        os.makedirs(output_dir, exist_ok=True)
        indexing_pipeline.export_index(rolling_index, os.path.join(output_dir, "index.csv"))


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Regulatory Uncertainty LLM Index Pipeline"
    )
    parser.add_argument(
        "--mode",
        default="full",
        choices=["full", "ingest", "preprocess", "embed", "classify", "index"],
        help="Pipeline execution mode"
    )
    parser.add_argument(
        "--date",
        default=datetime.now().date().isoformat(),
        help="Processing date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Initialize and run pipeline
    pipeline = RegulatoryUncertaintyPipeline()
    pipeline.run(mode=args.mode)


if __name__ == "__main__":
    main()
