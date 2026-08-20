FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONPATH=/app

WORKDIR /app

COPY langgraph_app/requirements.txt /app/langgraph_app/requirements.txt
RUN pip install --no-cache-dir -r /app/langgraph_app/requirements.txt

COPY langgraph_app /app/langgraph_app
COPY agents /app/agents

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn langgraph_app.api:app --host 0.0.0.0 --port ${PORT:-8080}"]
