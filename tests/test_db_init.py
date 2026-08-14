from sqlalchemy import inspect

from app.core.database import get_engine, init_db


def test_init_db_creates_app_tables(tmp_path):
    db_file = tmp_path / "db" / "init_test.db"
    engine = get_engine(str(db_file))
    # init_db should import models and create their tables
    init_db(engine, create_tables=True)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    # The app defines at least these tables
    assert "accounts" in tables, f"expected 'accounts' in {tables}"
    assert "ideas" in tables, f"expected 'ideas' in {tables}"
