"""
Semantic chunking module for text documents.

Implements intelligent text chunking that preserves semantic boundaries
rather than naive fixed-size chunks. Supports overlap for context preservation.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

from loguru import logger
import numpy as np


@dataclass
class TextChunk:
    """Data class for text chunks."""
    chunk_id: str
    text: str
    source_doc_id: str
    chunk_index: int
    start_char: int
    end_char: int
    tokens: int
    metadata: Dict


class SemanticChunker:
    """
    Performs semantic chunking on documents.

    Strategies:
    1. Sentence-based with overlap
    2. Paragraph-based
    3. Hybrid (respects sentence boundaries within chunk size limit)
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 100, strategy: str = "hybrid"):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in tokens (~4 chars per token)
            overlap: Number of overlapping characters between chunks
            strategy: "sentence", "paragraph", or "hybrid"
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy
        self.char_per_token = 4  # Approximation

        logger.info(f"Initialized SemanticChunker (strategy={strategy}, chunk_size={chunk_size})")

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Improved sentence boundary detection
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_by_sentences(self, text: str, doc_id: str) -> List[TextChunk]:
        """Chunk text by respecting sentence boundaries."""
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = ""
        start_char = 0
        chunk_index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size * self.char_per_token:
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, doc_id, chunk_index, start_char
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                # Start new chunk with overlap
                current_chunk = sentence
                start_char += len(current_chunk) - self.overlap
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(current_chunk, doc_id, chunk_index, start_char)
            chunks.append(chunk)

        logger.debug(f"Created {len(chunks)} chunks from document {doc_id}")
        return chunks

    def chunk_by_paragraphs(self, text: str, doc_id: str) -> List[TextChunk]:
        """Chunk text by paragraphs (separated by blank lines)."""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []

        current_chunk = ""
        start_char = 0
        chunk_index = 0

        for para in paragraphs:
            if not para.strip():
                continue

            if len(current_chunk) + len(para) > self.chunk_size * self.char_per_token:
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk, doc_id, chunk_index, start_char
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                current_chunk = para
                start_char += len(current_chunk) - self.overlap
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunk = self._create_chunk(current_chunk, doc_id, chunk_index, start_char)
            chunks.append(chunk)

        logger.debug(f"Created {len(chunks)} paragraph chunks from document {doc_id}")
        return chunks

    def chunk_hybrid(self, text: str, doc_id: str) -> List[TextChunk]:
        """Hybrid chunking: respects sentences but groups them into target size."""
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0
        start_char = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size * self.char_per_token and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                chunk = self._create_chunk(chunk_text, doc_id, chunk_index, start_char)
                chunks.append(chunk)
                chunk_index += 1

                # Reset with overlap
                current_chunk = [sentence]
                current_length = sentence_length
                start_char += len(chunk_text) - self.overlap
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk = self._create_chunk(chunk_text, doc_id, chunk_index, start_char)
            chunks.append(chunk)

        logger.debug(f"Created {len(chunks)} hybrid chunks from document {doc_id}")
        return chunks

    def _create_chunk(self, text: str, doc_id: str, index: int, start_char: int) -> TextChunk:
        """Create a TextChunk object."""
        chunk_id = f"{doc_id}_chunk_{index}"
        tokens = len(text) // self.char_per_token
        end_char = start_char + len(text)

        return TextChunk(
            chunk_id=chunk_id,
            text=text,
            source_doc_id=doc_id,
            chunk_index=index,
            start_char=start_char,
            end_char=end_char,
            tokens=tokens,
            metadata={
                "chunk_strategy": self.strategy,
                "char_count": len(text),
                "token_count": tokens
            }
        )

    def chunk_document(self, text: str, doc_id: str) -> List[TextChunk]:
        """
        Chunk a document using the configured strategy.

        Args:
            text: Document text
            doc_id: Document identifier

        Returns:
            List of TextChunk objects
        """
        if self.strategy == "sentence":
            return self.chunk_by_sentences(text, doc_id)
        elif self.strategy == "paragraph":
            return self.chunk_by_paragraphs(text, doc_id)
        else:  # hybrid
            return self.chunk_hybrid(text, doc_id)


class ChunkingPipeline:
    """End-to-end chunking pipeline for document processing."""

    def __init__(self, chunk_size: int = 512, overlap: int = 100):
        self.chunker = SemanticChunker(chunk_size=chunk_size, overlap=overlap, strategy="hybrid")
        logger.info(f"Initialized ChunkingPipeline")

    def process_documents(self, documents: List[Dict]) -> List[TextChunk]:
        """
        Process multiple documents.

        Args:
            documents: List of document dicts with 'id' and 'content' keys

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            doc_id = doc.get("id", "unknown")
            content = doc.get("content", "")

            if not content:
                logger.warning(f"Document {doc_id} has no content")
                continue

            chunks = self.chunker.chunk_document(content, doc_id)
            all_chunks.extend(chunks)

        logger.info(f"Processed {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks


if __name__ == "__main__":
    # Example usage
    sample_text = """
    The Federal Reserve Board announced new regulatory guidance.

    This guidance addresses the implementation of recent legislative changes.
    Banks must comply with the new requirements by Q3 2026.

    Specifically, institutions are required to enhance their risk management frameworks.
    The guidance covers credit risk, market risk, and operational risk dimensions.
    """

    chunker = SemanticChunker(chunk_size=50, strategy="hybrid")
    chunks = chunker.chunk_document(sample_text, "test_doc_001")

    for chunk in chunks:
        print(f"Chunk {chunk.chunk_index}: {chunk.text[:80]}...")
