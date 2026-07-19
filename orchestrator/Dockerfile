FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ORCHESTRATOR_DATA_DIR=/app/data

WORKDIR /app

RUN addgroup --system orchestrator && adduser --system --ingroup orchestrator orchestrator

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static
COPY prompts.py ./prompts.py
COPY create_agents.py ./create_agents.py
RUN mkdir -p /app/data && chown -R orchestrator:orchestrator /app

USER orchestrator
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["python", "create_agents.py", "--serve"]
