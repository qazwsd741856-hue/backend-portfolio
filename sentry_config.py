import os
import sentry_sdk

def setup_sentry():
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=os.getenv("APP_ENV")
    )