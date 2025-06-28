FROM python:3.12-slim-bookworm

RUN \
  apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  python3-dev

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /app

COPY web/requirements.txt /app/web/requirements.txt

RUN \
  pip install pip -U && \
  pip install --no-cache-dir -r web/requirements.txt

COPY . /app

STOPSIGNAL SIGINT

# ENTRYPOINT ["uvicorn"]
# CMD ["main:app"]
