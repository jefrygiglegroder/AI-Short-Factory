import tempfile
from app.repositories import account_repository
from app.core.database import get_engine, init_db, Base


def test_account_crud(tmp_path):
    db_file = tmp_path / "db" / "test_accounts.db"
    engine = get_engine(str(db_file))
    init_db(engine, create_tables=True)

    # Create account
    acct = account_repository.create_account(platform="youtube", name="acct1", description="desc")
    assert acct.id is not None
    assert acct.name == "acct1"

    # List accounts
    accts = account_repository.list_accounts()
    assert any(a.id == acct.id for a in accts)

    # Get account
    fetched = account_repository.get_account(acct.id)
    assert fetched is not None
    assert fetched.name == "acct1"
