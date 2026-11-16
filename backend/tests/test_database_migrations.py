import json

from sqlalchemy import create_engine, inspect, text

from backend.database import init_db


def test_init_db_adds_resume_analysis_column_without_losing_existing_data(tmp_path):
    database_path = tmp_path / "legacy.sqlite"
    legacy_engine = create_engine(f"sqlite:///{database_path}")
    try:
        with legacy_engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE candidate_profiles "
                    "(id VARCHAR(36) PRIMARY KEY, summary TEXT)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO candidate_profiles (id, summary) "
                    "VALUES ('legacy-profile', 'Existing profile summary')"
                )
            )

        init_db(legacy_engine)

        columns = {
            column["name"]
            for column in inspect(legacy_engine).get_columns("candidate_profiles")
        }
        assert "resume_analysis" in columns
        with legacy_engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT summary, resume_analysis FROM candidate_profiles "
                    "WHERE id = 'legacy-profile'"
                )
            ).one()
        assert row.summary == "Existing profile summary"
        assert json.loads(row.resume_analysis) == {}
    finally:
        legacy_engine.dispose()
