import logging
import json
from datetime import datetime, timezone
from context_var import request_id

# def setup_logging():
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
#         force=True
#     )

class RequestIdFilter(logging.Filter):
    def filter(self,record):
        record.request_id=request_id.get()
        return True
class JsonFormatter(logging.Formatter):
    def format(self,record):
        excluded_attrs=set(logging.LogRecord(
            name="",
            level=0,
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None).__dict__.keys())
        excluded_attrs.add("request_id")

        log_data={"timestamp":datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                  "level":record.levelname,
                  "request_id":record.request_id,
                  "logger":record.name,
                  "message":record.getMessage()}
        for key,value in record.__dict__.items():
            if key not in excluded_attrs:
                log_data[key]=value
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data,default=str)
    
def setup_logging():
    root_logger=logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_handler=logging.StreamHandler()
    # root_formatter=logging.Formatter("%(asctime)s | %(levelname)s | %(request_id)s | %(name)s | %(message)s")
    root_formatter=JsonFormatter()
    root_filter=RequestIdFilter()

    root_handler.addFilter(root_filter)
    root_handler.setFormatter(root_formatter)
    root_logger.addHandler(root_handler)
