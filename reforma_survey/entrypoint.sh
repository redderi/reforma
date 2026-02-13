#!/bin/sh
set -e

dockerize \
    -wait tcp://survey_postgres:5432 \
    -wait tcp://rabbitmq:5672 \
    -wait tcp://elasticsearch:9200 \
    -timeout 120s \
    -wait-retry-interval 5s

exec uvicorn reforma_survey.main:app --host 0.0.0.0 --port 8000 --root-path /api/survey_service
