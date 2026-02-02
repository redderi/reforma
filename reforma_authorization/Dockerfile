FROM python:3.12-slim

WORKDIR /reforma_authorization

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* /reforma_authorization/

RUN pip install --no-cache-dir "poetry>=1.6.0"

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY . /reforma_authorization

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "src.reforma_authorization.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
