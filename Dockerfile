FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy application code and entrypoint
COPY src/ /app/
COPY entrypoint.sh /app/entrypoint.sh

# install Python deps
RUN python -m pip install --upgrade pip setuptools \
    && python -m pip install --no-cache-dir requests cryptography

RUN chmod +x /app/check_ip.py /app/entrypoint.sh

VOLUME ["/data"]

ENTRYPOINT ["/app/entrypoint.sh"]