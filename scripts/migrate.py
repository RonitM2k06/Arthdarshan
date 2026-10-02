"""Apply database migrations and sync static content (concepts, scenarios, lessons, quizzes, simulations, knowledge base)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from ai.rag import engine as rag
    from apps.api.config import get_settings
    from apps.api.services.seed import sync_content
    from database import session as dbs

    s = get_settings()
    dbs.init_engine(s.database_url)
    dbs.run_migrations(s.database_url)
    with dbs.session_scope() as db:
        print("content:", sync_content(db))
        print("knowledge base:", rag.ingest(db, with_embeddings=False))
    print("database ready:", s.database_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
