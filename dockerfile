FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.dev.txt .
ARG ENVIRONMENT=production
RUN if [ "$ENVIRONMENT" = "development" ]; then\
        pip install --no-cache-dir -r requirements.dev.txt;\
    else\
        pip install --no-cache-dir -r requirements.txt;\
    fi
COPY . .
RUN useradd --create-home appuser
USER appuser
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]