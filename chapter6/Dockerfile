# New versions of Python may be available
# Given OTel Python only supports supported version of Python,
# the version may need to be increased to a supported version.

FROM python:3.9-slim

# Default settings

ENV SERVER_APP=${SERVER_APP:-server.py}
ENV SERVER_HOST=${SERVER_HOST:-0.0.0.0}
ENV SERVER_PORT=${SERVER_PORT:-8080}
ENV OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME}
WORKDIR /app

# Build commands

COPY . .

RUN apt-get update -y && apt-get install -y gcc
RUN pip3 install --upgrade pip # Optional, but recommended
RUN python3 -m pip install --upgrade setuptools wheel # Optional, but recommended

RUN pip3 install Flask Werkzeug requests paste waitress

# Run commands
# Note: execution form will not work due to dynamic variable
# Note: exec is required in order for Ctrl+C to be respected

CMD exec python3 ${SERVER_APP}
