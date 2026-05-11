"""
Regulatory documents ingestion module.

Handles parsing and extraction from regulatory documents, SEC filings,
Fed communications, and official regulatory notices.
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

import requests
from bs4 import BeautifulSoup
import pandas as pd
from loguru import logger


@dataclass
class RegulatoryDocument:
    """Data class for regulatory documents."""
    doc_id: str
    source: str
    title: str
    content: str
    publish_date: datetime
    url: str
    doc_type: str  # e.g., "SEC_FILING", "FED_STATEMENT", "REGULATORY_NOTICE"
    institution: str  # e.g., "SEC", "FED", "OCC", "FDIC"
    metadata: Dict


class RegulatoryDocumentScraper:
    """
    Scrapes and parses regulatory documents from official sources.

    Supports:
    - SEC Edgar (10-K, 10-Q, 8-K, S-1 filings)
    - Federal Reserve (speeches, statements, minutes)
    - OCC (guidance, bulletins)
    - FDIC (notices)
    - EBA (European Banking Authority)
    """

    def __init__(self, cache_dir: str = "./data/raw/"):
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info(f"Initialized RegulatoryDocumentScraper with cache at {cache_dir}")

    def scrape_sec_edgar(self, ticker: str, doc_type: str = "10-K", limit: int = 5) -> List[RegulatoryDocument]:
        """
        Scrape SEC Edgar filings for a given ticker.

        Args:
            ticker: Stock ticker symbol
            doc_type: Type of filing (10-K, 10-Q, 8-K, S-1)
            limit: Maximum number of documents to retrieve

        Returns:
            List of RegulatoryDocument objects
        """
        logger.info(f"Scraping SEC Edgar for {ticker} ({doc_type})")

        documents = []
        try:
            # API endpoint for SEC Edgar
            base_url = f"https://data.sec.gov/submissions/CIK{ticker}.json"
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            filings = data.get("filings", {}).get("recent", {})

            for idx, filing in enumerate(filings.get("form", [])):
                if idx >= limit or filing != doc_type:
                    continue

                doc_id = hashlib.md5(f"{ticker}_{filing}_{idx}".encode()).hexdigest()
                doc = RegulatoryDocument(
                    doc_id=doc_id,
                    source="SEC_EDGAR",
                    title=f"{ticker} {doc_type}",
                    content="[Content to be fetched]",  # Would fetch full document
                    publish_date=datetime.now(),
                    url=f"https://sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}",
                    doc_type=doc_type,
                    institution="SEC",
                    metadata={"ticker": ticker, "cik": ticker}
                )
                documents.append(doc)

        except Exception as e:
            logger.error(f"Error scraping SEC Edgar for {ticker}: {e}")

        return documents

    def scrape_fed_statements(self, limit: int = 10) -> List[RegulatoryDocument]:
        """Scrape Federal Reserve statements and communications."""
        logger.info(f"Scraping Federal Reserve statements (limit={limit})")

        documents = []
        try:
            # Federal Reserve Board press releases and statements
            base_url = "https://www.federalreserve.gov/newsevents/pressreleases/"
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Parse press releases
            for idx, article in enumerate(soup.find_all('article', limit=limit)):
                try:
                    title = article.find('h3')
                    if not title:
                        continue

                    doc_id = hashlib.md5(title.text.encode()).hexdigest()
                    doc = RegulatoryDocument(
                        doc_id=doc_id,
                        source="FEDERAL_RESERVE",
                        title=title.text,
                        content=article.get_text(),
                        publish_date=datetime.now(),
                        url=base_url,
                        doc_type="FED_STATEMENT",
                        institution="FED",
                        metadata={"statement_type": "press_release"}
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error parsing Federal Reserve article: {e}")

        except Exception as e:
            logger.error(f"Error scraping Federal Reserve: {e}")

        return documents

    def save_documents(self, documents: List[RegulatoryDocument]) -> None:
        """Save documents to cache directory."""
        os.makedirs(self.cache_dir, exist_ok=True)

        # Save as JSON-like structure
        for doc in documents:
            safe_filename = doc.doc_id + ".txt"
            filepath = os.path.join(self.cache_dir, safe_filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {doc.title}\n")
                f.write(f"Source: {doc.source}\n")
                f.write(f"Date: {doc.publish_date}\n")
                f.write(f"URL: {doc.url}\n")
                f.write(f"---\n")
                f.write(doc.content)

        logger.info(f"Saved {len(documents)} documents to {self.cache_dir}")

    def load_documents_from_cache(self) -> List[RegulatoryDocument]:
        """Load previously cached documents."""
        documents = []

        if not os.path.exists(self.cache_dir):
            return documents

        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.cache_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                doc_id = filename.replace('.txt', '')
                # Parse metadata from content
                lines = content.split('\n')
                title = lines[0].replace('Title: ', '') if lines else 'Unknown'

                doc = RegulatoryDocument(
                    doc_id=doc_id,
                    source="CACHED",
                    title=title,
                    content=content,
                    publish_date=datetime.now(),
                    url="",
                    doc_type="CACHED_DOC",
                    institution="UNKNOWN",
                    metadata={}
                )
                documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents from cache")
        return documents


if __name__ == "__main__":
    scraper = RegulatoryDocumentScraper()

    # Example: Scrape Fed statements
    fed_docs = scraper.scrape_fed_statements(limit=5)
    logger.info(f"Retrieved {len(fed_docs)} Federal Reserve documents")

    # Save to cache
    scraper.save_documents(fed_docs)
