#!/usr/bin/env python3
"""
Helper script to organize manually downloaded Charlotte, NC documents.

After downloading deeds, mortgages, etc. from https://www.meckdb.org/,
use this script to organize them by property/transaction.

Usage:
    python scripts/organize_charlotte_docs.py --input ~/Downloads/deeds --output sample-docs/charlotte_nc
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def organize_documents(input_dir: str, output_dir: str):
    """
    Organize downloaded documents into a closing package structure.
    
    Expected filenames (from meckdb.org):
    - Deed_[Book]_[Page]_[Description].pdf
    - Mortgage_[Book]_[Page]_[Description].pdf
    - etc.
    """
    input_path = Path(input_dir).expanduser()
    output_path = Path(output_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory not found: {input_path}")
        return
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Input:  {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Find all PDFs
    pdfs = list(input_path.glob("**/*.pdf"))
    logger.info(f"Found {len(pdfs)} PDF files")
    
    if not pdfs:
        logger.warning("No PDF files found!")
        logger.info("Make sure downloaded files are in: " + str(input_path))
        return
    
    # Copy to output, maintain structure
    organized = {
        "deeds": [],
        "mortgages": [],
        "titles": [],
        "other": [],
    }
    
    for pdf in pdfs:
        dest = output_path / pdf.name
        
        # Determine category
        category = "other"
        if "deed" in pdf.name.lower():
            category = "deeds"
        elif "mort" in pdf.name.lower():
            category = "mortgages"
        elif "title" in pdf.name.lower():
            category = "titles"
        
        # Copy file
        dest.write_bytes(pdf.read_bytes())
        logger.info(f"✓ {pdf.name} → {category}/")
        organized[category].append(str(dest.relative_to(output_path)))
    
    # Save manifest
    manifest = {
        "location": "Charlotte, NC (Mecklenburg County)",
        "organized_at": datetime.now().isoformat(),
        "total_documents": len(pdfs),
        "by_type": organized,
    }
    
    manifest_path = output_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    logger.info(f"\n✓ Organized {len(pdfs)} documents")
    logger.info(f"✓ Manifest: {manifest_path}")
    logger.info("\nNext steps:")
    logger.info(f"1. Verify documents: ls -la {output_path}")
    logger.info("2. Upload to CloseCheck: http://localhost:5173")


def main():
    parser = argparse.ArgumentParser(
        description="Organize manually downloaded Charlotte closing documents"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing downloaded PDFs (e.g., ~/Downloads/)",
    )
    parser.add_argument(
        "--output",
        default="sample-docs/charlotte_nc",
        help="Output directory for organized documents",
    )
    
    args = parser.parse_args()
    organize_documents(args.input, args.output)


if __name__ == "__main__":
    main()
