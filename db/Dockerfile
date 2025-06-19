FROM python:3.12-slim-bookworm

RUN \
  apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  python3-dev

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /app
COPY . /app

RUN \
  pip install pip -U && \
  pip install --no-cache-dir -r requirements.txt

STOPSIGNAL SIGINT

# ENTRYPOINT ["python"]
# CMD ["-m", "main"]
