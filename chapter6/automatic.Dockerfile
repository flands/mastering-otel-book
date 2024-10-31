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

# The quotations are required else the package will not be found with ZSH shells
# If the command still does not work, ensure straight quotations are being used
# as curly quotations will also not work.
# This command is equivalent to:
#  pip install opentelemetry-distro opentelemetry-exporter-otlp
RUN pip3 install "opentelemetry-distro[otlp]"

# If you only plan to use the console exporter (example: no OTel Collector),
# you can use this command instead:
#RUN pip3 install opentelemetry-distro

# Easiest to get started but installs more instrumentation packages than needed
#RUN opentelemetry-bootstrap -a install

# Requires manually determining which instrumentation packages are needed
# Instrumentation packages are available in the OTel Python Contrib repository
# https://github.com/open-telemetry/opentelemetry-python-
# contrib/tree/main/instrumentation
RUN pip3 install opentelemetry-instrumentation-flask
RUN pip3 install opentelemetry-instrumentation-requests
RUN pip3 install opentelemetry-instrumentation-logging

# Run commands
# Note: execution form will not work due to dynamic variable
# Note: exec is required in order for Ctrl+C to be respected

#CMD exec python3 ${SERVER_APP}

#CMD OTEL_RESOURCE_ATTRIBUTES=service.name=${OTEL_SERVICE_NAME} \
#    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=process \
#    exec opentelemetry-instrument --metrics_exporter none \
#         python3 ${SERVER_APP}

# An equivalent and more specific way to run the command:
#CMD OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME} \
#    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=process \
#    exec opentelemetry-instrument --traces_exporter otlp \
#         --metrics_exporter otlp python3 ${SERVER_APP}

# An equivalent way to run the command with only environment variables:
#CMD OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME} \
#    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=process \
#    OTEL_METRICS_EXPORTER=none \
#    exec opentelemetry-instrument python3 ${SERVER_APP}

# If you wish to use the console exporter instead (example: no OTel Collector),
# use this command instead:
#CMD OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME} \
#    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=process \
#    exec opentelemetry-instrument --traces_exporter console \
#         --metrics_exporter none python3 ${SERVER_APP}

CMD OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME} \
    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS=process \
    exec opentelemetry-instrument --metrics_exporter none \
         python3 ${SERVER_APP}
