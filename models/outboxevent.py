from sqlalchemy import Column, Integer, String, DateTime, JSON,func
from database import Base


class OutboxEvent(Base):
    __tablename__ = "OutboxEvent"

    id=Column(Integer,primary_key=True)
    event_type=Column(String,nullable=False)
    payload=Column(JSON,nullable=False)
    status=Column(String,nullable=False,server_default="pending")
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
    sent_at=Column(DateTime(timezone=True),nullable=True)



 