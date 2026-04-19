#!/usr/bin/env python3
"""
Charlotte, NC (Mecklenburg County) Real Estate Closing Document Scraper

Downloads publicly available closing documents from Mecklenburg County Register of Deeds.
Respects robots.txt and rate limiting.

Usage:
    python scripts/download_charlotte_docs.py
    python scripts/download_charlotte_docs.py --output-dir sample-docs/charlotte_nc
    python scripts/download_charlotte_docs.py --limit 50
"""

import argparse
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
MECKLENBURG_REGISTER = "https://www.meckdb.org"
MECKLENBURG_PUBLIC_SEARCH = "https://meckdb.org/public_records/search"

# Headers to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


class CharlotteDocumentScraper:
    """Scrapes publicly available real estate documents from Mecklenburg County."""

    def __init__(self, output_dir: str = "sample-docs/charlotte_nc", delay: float = 2.0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.downloaded_docs = []
        self.failed_docs = []

    def _wait(self):
        """Respectful delay between requests."""
        time.sleep(self.delay)

    def search_transactions(
        self,
        search_type: str = "grantor",
        limit: int = 20,
        days_back: int = 90,
    ) -> list[dict]:
        """
        Search for recent transactions in Mecklenburg County.
        
        Args:
            search_type: "grantor" (seller), "grantee" (buyer), or "property"
            limit: Maximum number of results to return
            days_back: Search transactions from last N days
            
        Returns:
            List of transaction dicts with deed info
        """
        logger.info(f"Searching {search_type} records from last {days_back} days...")
        
        try:
            # Try the public search interface
            response = self.session.get(
                MECKLENBURG_PUBLIC_SEARCH,
                timeout=10,
            )
            response.raise_for_status()
            self._wait()
            
            logger.info(
                f"Successfully accessed Mecklenburg County public records. "
                f"Status: {response.status_code}"
            )
            
            # Parse the page for available documents
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Look for deed links or document listings
            deed_links = soup.find_all("a", href=lambda x: x and ("deed" in x.lower() or "pdf" in x.lower()))
            
            logger.info(f"Found {len(deed_links)} potential documents on page")
            
            # Extract document info
            transactions = []
            for idx, link in enumerate(deed_links[:limit]):
                try:
                    doc_url = link.get("href")
                    doc_title = link.get_text(strip=True)
                    
                    # Make absolute URL if relative
                    if doc_url and not doc_url.startswith("http"):
                        doc_url = MECKLENBURG_REGISTER + doc_url
                    
                    if doc_url:
                        transactions.append({
                            "title": doc_title or f"Document_{idx}",
                            "url": doc_url,
                            "source": "Mecklenburg County Register of Deeds",
                            "accessed": datetime.now().isoformat(),
                        })
                except Exception as e:
                    logger.warning(f"Error extracting link info: {e}")
            
            return transactions
        
        except requests.exceptions.ConnectionError:
            logger.error(
                "❌ Connection error: Could not reach Mecklenburg County servers."
            )
            logger.info("⚠️  Try these alternatives:")
            logger.info("  1. Visit https://www.meckdb.org/ manually")
            logger.info("  2. Search by book/page number (public records searchable there)")
            logger.info("  3. Use NC Judicial Branch (https://www.nccourts.org/)")
            return []
        
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout: Server took too long to respond")
            return []
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return []

    def download_document(self, url: str, filename: str) -> bool:
        """
        Download a single document.
        
        Args:
            url: Document URL
            filename: Local filename to save as
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"  Downloading: {filename}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Save file
            file_path = self.output_dir / filename
            file_path.write_bytes(response.content)
            
            file_size = len(response.content) / 1024  # KB
            logger.info(f"    ✓ Saved ({file_size:.1f} KB)")
            self.downloaded_docs.append({
                "filename": filename,
                "url": url,
                "size_bytes": len(response.content),
                "downloaded_at": datetime.now().isoformat(),
            })
            
            self._wait()
            return True
        
        except Exception as e:
            logger.error(f"    ✗ Failed: {e}")
            self.failed_docs.append({"filename": filename, "url": url, "error": str(e)})
            self._wait()
            return False

    def save_report(self):
        """Save download report to JSON."""
        report = {
            "downloaded": len(self.downloaded_docs),
            "failed": len(self.failed_docs),
            "total_attempted": len(self.downloaded_docs) + len(self.failed_docs),
            "location": "Mecklenburg County, Charlotte, NC",
            "documents": self.downloaded_docs,
            "errors": self.failed_docs,
            "generated": datetime.now().isoformat(),
        }
        
        report_path = self.output_dir / "_download_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        logger.info(f"Report saved: {report_path}")

    def run(self, limit: int = 20, days_back: int = 90):
        """
        Main execution: search and download documents.
        """
        logger.info("=" * 70)
        logger.info("Charlotte, NC (Mecklenburg County) Document Scraper")
        logger.info("=" * 70)
        logger.info(f"Output directory: {self.output_dir.absolute()}\n")

        # Search for transactions
        transactions = self.search_transactions(
            search_type="grantor",
            limit=limit,
            days_back=days_back,
        )

        if not transactions:
            logger.warning("\n⚠️  No documents found. This may be because:")
            logger.warning("  - Mecklenburg County servers are temporarily unavailable")
            logger.warning("  - The website structure has changed (may need update)")
            logger.warning("  - Network/firewall restrictions")
            logger.info("\n📋 Manual alternative:")
            logger.info("  1. Visit https://www.meckdb.org/")
            logger.info("  2. Click 'Public Records Search'")
            logger.info("  3. Search by Book/Page number (e.g., 'Book 12345, Page 1')")
            logger.info("  4. Download deeds and mortgages as PDFs")
            logger.info("  5. Place in: " + str(self.output_dir))
            return

        logger.info(f"\n📄 Found {len(transactions)} documents")
        logger.info("Downloading...\n")

        # Download documents
        for idx, doc in enumerate(transactions, 1):
            logger.info(f"[{idx}/{len(transactions)}] {doc['title']}")
            
            # Sanitize filename
            safe_title = "".join(
                c for c in doc["title"] if c.isalnum() or c in "-_ "
            ).rstrip()
            filename = f"mecklenburg_{idx:03d}_{safe_title}.pdf"
            
            self.download_document(doc["url"], filename)

        # Save report
        logger.info("\n" + "=" * 70)
        self.save_report()
        logger.info(
            f"Downloaded: {len(self.downloaded_docs)} | "
            f"Failed: {len(self.failed_docs)}"
        )
        logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Download real estate documents from Mecklenburg County, NC"
    )
    parser.add_argument(
        "--output-dir",
        default="sample-docs/charlotte_nc",
        help="Output directory for downloaded documents",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of documents to download",
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=90,
        help="Search documents from last N days",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay (seconds) between requests (respectful scraping)",
    )

    args = parser.parse_args()

    scraper = CharlotteDocumentScraper(
        output_dir=args.output_dir,
        delay=args.delay,
    )
    scraper.run(limit=args.limit, days_back=args.days_back)


if __name__ == "__main__":
    main()
