from celery import Celery
import os 
from logging_config import RequestIdFilter,JsonFormatter

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from models.processedevent import ProcessedEvent
from sqlalchemy.exc import IntegrityError
from context_var import request_id
import logging
from celery.signals import after_setup_logger
from sentry_config import setup_sentry

setup_sentry()
logger=logging.getLogger(__name__)
DATABASE_URL=os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL沒設定")
worker_engine=create_engine(DATABASE_URL)

WorkerSessionLocal=sessionmaker(bind=worker_engine)

celery_app=Celery("backend-portfolio",broker="redis://redis:6379/1")

celery_app.conf.task_routes={"celery_app.send_order_notification":{"queue":"notifications"}}
celery_app.conf.task_reject_on_worker_lost = True

@celery_app.task(autoretry_for=(Exception,),max_retries=3,retry_backoff=True,acks_late=True)
def send_order_notification(event_id:int,order_id:int,event_request_id:str):


    with WorkerSessionLocal() as db:
        token=request_id.set(event_request_id)
        try:
            logger.info("Processing notification",extra={"event_id":event_id, "order_id":order_id})
            processedevent=ProcessedEvent(event_id=event_id)
            db.add(processedevent)
            db.commit()
            logger.info("Notification processed successfully",extra= {"event_id":event_id, "order_id":order_id})
        except IntegrityError:
            db.rollback()

            logger.warning("Duplicate event skipped",extra={"event_id":event_id, "order_id":order_id})
            return
        finally:
            request_id.reset(token)
        

    
    
@after_setup_logger.connect
def configure_celery_logging(logger, **kwargs):

    # formatter = logging.Formatter(
    #     "%(asctime)s | %(levelname)s | %(request_id)s | %(name)s | %(message)s"
    # )
    formatter=JsonFormatter()
    request_id_filter = RequestIdFilter()
    for handler in logger.handlers:
        handler.addFilter(request_id_filter)
        handler.setFormatter(formatter)