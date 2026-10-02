import os
import tempfile
from pathlib import Path

import pytest

# Isolated DB per test session; set BEFORE the app imports settings.
_TMP = Path(tempfile.mkdtemp(prefix="arth_test_"))
os.environ["ARTH_DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["ARTH_LLM_ENABLED"] = "0"          # tests never depend on a local LLM
os.environ["ARTH_ENABLE_EMBEDDINGS"] = "0"    # keyword retrieval in unit tests (embeddings tested separately)
os.environ["ARTH_AUTO_MIGRATE"] = "1"


@pytest.fixture(scope="session")
def scenarios():
    from apps.api.services.content import load_scenarios
    return load_scenarios()
