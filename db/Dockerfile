FROM python:3.12-slim-bookworm

RUN \
  apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  python3-dev

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /app

COPY db/requirements.txt /app/db/requirements.txt

RUN \
  pip install pip -U && \
  pip install --no-cache-dir -r db/requirements.txt

COPY . /app

STOPSIGNAL SIGINT

# ENTRYPOINT ["python"]
# CMD ["-m", "main"]
