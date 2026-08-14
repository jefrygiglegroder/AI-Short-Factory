from app.repositories import account_repository, idea_repository
from app.core.database import get_engine, init_db


def test_idea_crud(tmp_path):
    db_file = tmp_path / "db" / "test_ideas.db"
    engine = get_engine(str(db_file))
    init_db(engine, create_tables=True)

    acct = account_repository.create_account(platform="yt", name="acct_ideas")
    idea = idea_repository.create_idea(account_id=acct.id, title="Idea 1", hook="Hook")

    assert idea.id is not None
    ideas = idea_repository.list_ideas_for_account(acct.id)
    assert any(i.id == idea.id for i in ideas)
