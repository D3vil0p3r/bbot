import sqlite3
from .base import ModuleTestBase


class TestSQLite(ModuleTestBase):
    targets = ["evilcorp.com"]

    def check(self, module_test, events):
        sqlite_output_file = module_test.scan.home / "output.sqlite"
        assert sqlite_output_file.exists(), "SQLite output file not found"

        # first connect with raw sqlite
        with sqlite3.connect(sqlite_output_file) as db:
            cursor = db.cursor()
            results = cursor.execute("SELECT * FROM event").fetchall()
            assert len(results) == 3, "No events found in SQLite database"
            results = cursor.execute("SELECT * FROM scan").fetchall()
            assert len(results) == 1, "No scans found in SQLite database"
            results = cursor.execute("SELECT * FROM target").fetchall()
            assert len(results) == 1, "No targets found in SQLite database"

        # then connect with bbot models
        from bbot.models.sql import Event
        from sqlmodel import create_engine, Session, select

        engine = create_engine(f"sqlite:///{sqlite_output_file}")

        with Session(engine) as session:
            statement = select(Event).where(Event.host == "evilcorp.com")
            event = session.exec(statement).first()
            assert event.host == "evilcorp.com", "Event host should match target host"
            assert event.data == "evilcorp.com", "Event data should match target host"