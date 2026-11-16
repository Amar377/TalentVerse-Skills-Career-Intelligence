import json

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect

from backend.database import CandidateProfileModel, init_db


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


def test_init_db_creates_sqlite_schema_and_persists_json_analysis(tmp_path):
    database_path = tmp_path / "new.sqlite"
    sqlite_engine = create_engine(f"sqlite:///{database_path}")
    try:
        init_db(sqlite_engine)

        assert "candidate_profiles" in inspect(sqlite_engine).get_table_names()
        column_type = CandidateProfileModel.__table__.c.resume_analysis.type
        assert column_type.compile(dialect=sqlite_engine.dialect).upper() == "JSON"

        with sqlite_engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO candidate_profiles (id, resume_analysis) "
                    "VALUES ('profile-json', :analysis)"
                ),
                {"analysis": '{"ats_score": 82}'},
            )
            result = connection.execute(
                text(
                    "SELECT resume_analysis FROM candidate_profiles "
                    "WHERE id = 'profile-json'"
                )
            ).scalar_one()
        assert result == '{"ats_score": 82}'
    finally:
        sqlite_engine.dispose()


def test_resume_analysis_json_type_compiles_for_postgresql():
    column_type = CandidateProfileModel.__table__.c.resume_analysis.type

    assert column_type.compile(dialect=postgresql_dialect()).upper() == "JSON"
