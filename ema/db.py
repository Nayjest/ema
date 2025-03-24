import os

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from microcore import ui

session: sessionmaker
db_engine: Engine
db_metadata: MetaData


def init_db(verbose=False):
    global session, db_engine, db_metadata

    db_engine = create_engine(os.getenv("DB_URL"), echo=verbose, future=True)
    session = sessionmaker(bind=db_engine)
    db_metadata = MetaData()
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    check_db_connection()


def check_db_connection():
    print("Checking database connection... ", end="")
    try:
        with session() as ses:
            ses.execute(text("SELECT 1")).fetchall()
    except OperationalError as e:
        print(ui.red(str(e)))
        exit()
    print(f"[{ui.green('OK')}]")


def sql(query: str):
    global session
    with session() as ses:
        result = ses.execute(text(query))
        try:
            rows = result.mappings().all()
        except Exception:
            rows = None
        ses.commit()
    return rows
