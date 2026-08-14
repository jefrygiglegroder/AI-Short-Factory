from app.core.database import get_engine, init_db, Base, session_scope
from sqlalchemy import Column, Integer, String


def test_init_db_and_session(tmp_path):
    db_file = tmp_path / "data" / "test.db"
    engine = get_engine(str(db_file))
    # init_db should create parent directory and (optionally) no tables yet
    init_db(engine, create_tables=False)
    assert db_file.parent.exists()

    # Define a simple model dynamically for testing
    class TestRow(Base):
        __tablename__ = "test_table"
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)

    # Create the table
    Base.metadata.create_all(engine)

    # Use the session context manager to insert and query
    with session_scope(engine) as s:
        row = TestRow(name="hello")
        s.add(row)
        s.flush()
        assert row.id is not None
        rid = row.id

    with session_scope(engine) as s:
        fetched = s.get(TestRow, rid)
        assert fetched is not None
        assert fetched.name == "hello"
