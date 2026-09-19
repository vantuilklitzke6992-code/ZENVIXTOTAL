import atexit
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import utils.db as db_module

_test_database_directory = Path(tempfile.mkdtemp(prefix="zenvix-tests-"))
test_database_path = _test_database_directory / "database.db"
db_module.DATABASE_PATH = str(test_database_path)


def _remove_test_database():
    shutil.rmtree(_test_database_directory, ignore_errors=True)


atexit.register(_remove_test_database)


def pytest_sessionfinish(session, exitstatus):
    _remove_test_database()
