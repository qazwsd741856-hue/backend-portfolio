from pydantic import BaseModel
from datetime import datetime

class OrderEventReturn(BaseModel):
    order_id:int
    event_id:int
    event_type:str
    status:str
    created_at:datetime
    sent_at:datetime | None
    processed:bool
    processed_at:datetime | None
