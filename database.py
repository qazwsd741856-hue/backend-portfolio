from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL 未設定")

engine=create_engine(DATABASE_URL)

SessionLocal=sessionmaker(bind=engine)

Base=declarative_base() 


def get_db():
    db=SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        
        