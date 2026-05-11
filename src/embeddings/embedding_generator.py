"""
Embedding generation module using Sentence Transformers.

Generates high-dimensional vector embeddings for text chunks
using state-of-the-art transformer models.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from loguru import logger
import torch


@dataclass
class TextEmbedding:
    """Data class for text embeddings."""
    chunk_id: str
    embedding: np.ndarray
    model_id: str
    dimension: int
    norm_embedding: Optional[np.ndarray] = None


class EmbeddingGenerator:
    """
    Generates embeddings for text chunks using Sentence Transformers.

    Models available:
    - all-MiniLM-L6-v2 (384 dims, fast, good for semantic search)
    - all-mpnet-base-v2 (768 dims, slower but better quality)
    - allenai/specter (768 dims, specialized for scientific documents)
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        batch_size: int = 32,
        normalize: bool = True
    ):
        """
        Initialize embedding generator.

        Args:
            model_name: Hugging Face model identifier
            device: "cpu" or "cuda"
            batch_size: Batch processing size
            normalize: Whether to L2-normalize embeddings
        """
        self.model_name = model_name
        self.device = device if torch.cuda.is_available() else "cpu"
        self.batch_size = batch_size
        self.normalize = normalize

        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=self.device)

        # Get embedding dimension
        test_embedding = self.model.encode(["test"], convert_to_numpy=True)
        self.embedding_dim = test_embedding.shape[1]

        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def encode_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Encode multiple texts to embeddings.

        Args:
            texts: List of text strings
            show_progress: Show progress bar

        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        logger.info(f"Encoding {len(texts)} texts")

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )

        if self.normalize:
            # L2 normalization
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-10)
            logger.debug("Applied L2 normalization")

        return embeddings

    def encode_chunk(self, text: str) -> np.ndarray:
        """Encode a single text chunk."""
        embedding = self.model.encode([text], convert_to_numpy=True)[0]

        if self.normalize:
            norm = np.linalg.norm(embedding)
            embedding = embedding / (norm + 1e-10)

        return embedding

    def encode_chunks_with_ids(
        self,
        chunks: List[Dict[str, str]]
    ) -> List[TextEmbedding]:
        """
        Encode chunks with their IDs.

        Args:
            chunks: List of dicts with 'id' and 'text' keys

        Returns:
            List of TextEmbedding objects
        """
        texts = [chunk["text"] for chunk in chunks]
        chunk_ids = [chunk["id"] for chunk in chunks]

        embeddings = self.encode_texts(texts)

        result = []
        for chunk_id, embedding in zip(chunk_ids, embeddings):
            text_emb = TextEmbedding(
                chunk_id=chunk_id,
                embedding=embedding,
                model_id=self.model_name,
                dimension=self.embedding_dim,
                norm_embedding=embedding if self.normalize else None
            )
            result.append(text_emb)

        return result

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Cosine similarity score [-1, 1]
        """
        # Ensure normalized for cosine similarity
        if self.normalize:
            return float(np.dot(emb1, emb2))
        else:
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            return float(np.dot(emb1, emb2) / (norm1 * norm2 + 1e-10))

    def semantic_search(
        self,
        query: str,
        embeddings: List[np.ndarray],
        chunk_ids: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find most similar chunks to a query.

        Args:
            query: Query text
            embeddings: List of embedding vectors
            chunk_ids: Corresponding chunk IDs
            top_k: Number of top results to return

        Returns:
            List of (chunk_id, similarity) tuples
        """
        query_emb = self.encode_chunk(query)
        embeddings_array = np.array(embeddings)

        # Cosine similarity
        similarities = embeddings_array @ query_emb

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [
            (chunk_ids[idx], float(similarities[idx]))
            for idx in top_indices
        ]

        return results


class EmbeddingCache:
    """Cache embeddings to disk to avoid recomputation."""

    def __init__(self, cache_dir: str = "./data/embeddings/"):
        self.cache_dir = cache_dir
        import os
        os.makedirs(cache_dir, exist_ok=True)

    def save(self, embeddings: List[TextEmbedding]) -> None:
        """Save embeddings to disk."""
        import json

        data = {
            "embeddings": [
                {
                    "chunk_id": emb.chunk_id,
                    "embedding": emb.embedding.tolist(),
                    "model_id": emb.model_id,
                    "dimension": emb.dimension
                }
                for emb in embeddings
            ]
        }

        filepath = f"{self.cache_dir}/embeddings.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)

        logger.info(f"Saved {len(embeddings)} embeddings to {filepath}")

    def load(self) -> List[TextEmbedding]:
        """Load embeddings from disk."""
        import json
        import os

        filepath = f"{self.cache_dir}/embeddings.json"
        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r') as f:
            data = json.load(f)

        embeddings = [
            TextEmbedding(
                chunk_id=emb["chunk_id"],
                embedding=np.array(emb["embedding"]),
                model_id=emb["model_id"],
                dimension=emb["dimension"]
            )
            for emb in data.get("embeddings", [])
        ]

        logger.info(f"Loaded {len(embeddings)} embeddings from cache")
        return embeddings


if __name__ == "__main__":
    # Example usage
    generator = EmbeddingGenerator(model_name="sentence-transformers/all-MiniLM-L6-v2")

    texts = [
        "The Federal Reserve announced new regulatory guidance.",
        "Banks must enhance their risk management frameworks.",
        "Economic policy changes affect financial markets."
    ]

    embeddings = generator.encode_texts(texts)
    print(f"Generated embeddings shape: {embeddings.shape}")

    # Test semantic search
    query = "What did the Fed say?"
    results = generator.semantic_search(query, embeddings.tolist(), list(range(len(texts))), top_k=2)
    print(f"Top results for '{query}': {results}")
