from sqlalchemy import Column, Integer, DateTime, func
from database import Base


class ProcessedEvent(Base):
    __tablename__ = "ProcessedEvent"

    id = Column(Integer, primary_key=True)

    event_id = Column(Integer,nullable=False,unique=True)

    processed_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now())