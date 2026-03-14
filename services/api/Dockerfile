FROM python:3.11-slim

WORKDIR /app

COPY python /app/python
COPY services/api /app/services/api

RUN pip install --no-cache-dir fastapi uvicorn pydantic jsonschema

ENV PYTHONPATH=/app/python

CMD ["uvicorn", "services.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
