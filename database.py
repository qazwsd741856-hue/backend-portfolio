from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
# from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
if ASYNC_DATABASE_URL is None:
    raise RuntimeError("ASYNC_DATABASE_URL 未設定")

# engine=create_engine(DATABASE_URL)
engine=create_async_engine(ASYNC_DATABASE_URL,echo=True)

# SessionLocal=sessionmaker(bind=engine)
SessionLocal=async_sessionmaker(bind=engine,expire_on_commit=False)

Base=declarative_base() 


# def get_db():
#     db=SessionLocal()
    
#     try:
#         yield db
#     finally:
#         db.close()
        
async def get_db():
    async with SessionLocal() as db:
        yield db