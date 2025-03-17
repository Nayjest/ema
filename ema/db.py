import os
from msilib import Table

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import sessionmaker

session: sessionmaker
db_engine: Engine
db_metadata: MetaData

def init_db():
    global session, db_engine, db_metadata
    db_engine = create_engine(os.getenv("DB_URL"), echo=True, future=True)
    session = sessionmaker(bind=db_engine)
    db_metadata = MetaData()
