"""Build FAISS vector index from portfolio content."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build portfolio RAG vector index")
    parser.add_argument("--force", action="store_true", help="Rebuild even if index exists")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()
        from app.rag.ingest import build_vectorstore

        build_vectorstore(force=args.force)
        print("Vector index built successfully.")
        return 0
    except Exception as exc:
        print(f"Failed to build index: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
