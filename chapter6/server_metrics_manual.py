from random import randint
from flask import Flask, request
from paste.translogger import TransLogger
from waitress import serve
import logging
import os

# Metric-specific OTel modules
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.metrics import (
    get_meter,
    set_meter_provider,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)

# Signal-agnostic OTel modules
from opentelemetry.instrumentation.wsgi import collect_request_attributes
from opentelemetry.sdk.resources import (
    get_aggregated_resources,
    ProcessResourceDetector,
    Resource,
)

SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
SERVER_PORT = os.getenv('SERVER_PORT', 8080)

app = Flask(__name__)
appname = os.path.splitext(os.path.basename(__file__))[0]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# One-time signal-agnostic OTel configuration
resource = get_aggregated_resources(
    [ProcessResourceDetector()],
    Resource.create({"service.name": appname}),
)

# One-time metric-specific OTel configuration
# Replace OTLPMetricExporter with ConsoleMetricExporter
# if not using the OTel Collector
exporter = OTLPMetricExporter()
#exporter = ConsoleMetricExporter()
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(
    metric_readers=[reader],
    resource=resource,
)
set_meter_provider(provider)

# OTel way to create a meter and a counter
meter = get_meter(
    "roll-dice",
    "0.1.2"
)
counter = meter.create_counter(
    "counter",
    description="count of dice rolls since start"
)


@app.route('/')
def return_hello():
    player = get_player('OTel Test')
    return 'Hello! Be sure to roll the dice at /rolldice'


@app.route("/rolldice")
def roll_dice():
    player = get_player()

    # Function-specific OTel metric creation
    attributes = collect_request_attributes(request.environ)
    attributes.update({"player": player})

    result = str(roll(attributes))
    logger.warning("%s is rolling the dice: %s", player, result)
    return result


def get_player(default=None):
    try:
        if default is None:
            default = 'Anonymous player'
            raise TypeError
    except TypeError:
        logger.warning("Player request arg not set")
    return request.args.get('player', default=default, type=str)


def roll(attributes):
    counter.add(
        1,
        attributes=attributes
    )

    return [randint(1, 6), randint(1, 6)]


if __name__ == "__main__":
    serve(TransLogger(app), host=SERVER_HOST, port=SERVER_PORT)
