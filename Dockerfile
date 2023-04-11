FROM python:3.9

WORKDIR /app
COPY . .

RUN python -m pip install .

CMD ["otus-scoring-api-server", "-r", "redis://redis:6379"]
