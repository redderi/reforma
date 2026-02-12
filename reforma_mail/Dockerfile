FROM python:3.12-slim

WORKDIR /app

# Устанавливаем необходимые пакеты и dockerize
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем dockerize
ENV DOCKERIZE_VERSION=v0.7.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Копируем приложение
COPY reforma_mail /app/reforma_mail

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/reforma_mail/requirements.txt

# Настройки Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/reforma_mail/src
EXPOSE 8000

# Копируем entrypoint
COPY reforma_mail/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Запуск через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
