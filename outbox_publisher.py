import asyncio 
from sqlalchemy import select 
from database import SessionLocal 
from models.outboxevent import OutboxEvent 
from celery_app import send_order_notification 
from datetime import datetime,timezone 
import logging,sentry_sdk
from context_var import request_id
from sentry_config import setup_sentry
from logging_config import setup_logging
setup_logging()

setup_sentry()

logger=logging.getLogger(__name__)

async def publish_one(): 
    async with SessionLocal() as db:
        stmt = (select(OutboxEvent).where(OutboxEvent.status == "pending").order_by(OutboxEvent.id).with_for_update(skip_locked=True).limit(1))
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if event is None:
            return False

        if event.event_type=="order_created": 
            order_id=event.payload["order_id"] 
            event_request_id=event.payload["request_id"]

            token=request_id.set(event_request_id)
            try:
                logger.info("Publishing OutboxEvent",
                             extra={"event_id":event.id,
                                    "event_type":event.event_type,
                                    "order_id":order_id, 
                                    "status":event.status}
                )   
                send_order_notification.delay(event.id,order_id,event_request_id) 
            
                event.status="sent" 
                event.sent_at=datetime.now(timezone.utc) 
                await db.commit() 
                return True
            except Exception as e:
                event_id=event.id
                await db.rollback()
                logger.exception("OutboxEvent publish failed",extra={"event_id":event_id})
                sentry_sdk.capture_exception(e)
                return False
            finally:
                request_id.reset(token)
        else:
            event.status = "failed"
            await db.commit()
            logger.warning("Unsupported OutboxEvent",extra={"event_id":event.id,"event_type":event.event_type})
            return True
        


# async def publish_outbox(): 
#     async with SessionLocal() as db: 
#         stmt = select(OutboxEvent).where( OutboxEvent.status == "pending" ) 
#         result = await db.execute(stmt) 
#         events = result.scalars().all() 
#         for event in events: 
#             try:
#                 print( f"id={event.id}," 
#                 f"type={event.event_type}, " 
#                 f"payload={event.payload}, " 
#                 f"status={event.status}",
#                 flush=True) 
#                 if event.event_type=="order_created": 
#                     order_id=event.payload["order_id"] 
#                     send_order_notification.delay(event.id,order_id) 

#                     # print(f"Event {event.id} 已送進 Redis，現在故意讓 Publisher crash")
#                     # raise Exception("模擬 Publisher 在 publish 成功後 crash")

#                     event.status="sent" 
#                     event.sent_at=datetime.now(timezone.utc) 
#                     await db.commit() 
#             except Exception as e:
#                 event_id=event.id
#                 await db.rollback()
#                 print(f"OutboxEvent {event_id} 發布失敗: {e}",
#                 flush=True)

async def main():
    while True:
        while await publish_one():
            pass
        await asyncio.sleep(5)

asyncio.run(main())