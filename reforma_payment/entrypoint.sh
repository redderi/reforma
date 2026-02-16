#!/bin/sh
set -e

dockerize \
    -wait tcp://payment_postgres:5432 \
    -wait tcp://rabbitmq:5672 \
    -timeout 120s \
    -wait-retry-interval 5s

exec uvicorn reforma_payment.main:app --host 0.0.0.0 --port 8000 --root-path /api/payment_service
