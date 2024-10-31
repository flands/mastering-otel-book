from random import randint
from flask import Flask, request
from paste.translogger import TransLogger
from waitress import serve
import logging
import os

# Trace-specific OTel modules
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.trace import set_tracer_provider

# Signal-agnostic OTel modules
from opentelemetry.instrumentation.flask import FlaskInstrumentor
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

# One-time trace-specific OTel configuration
# Replace OTLPSpanExporter with ConsoleSpanExporter
# if not using the OTel Collector
set_tracer_provider(TracerProvider(
    active_span_processor=BatchSpanProcessor(OTLPSpanExporter()),
    resource=resource,
))

# OTel programmatic instrumentation
instrumentor = FlaskInstrumentor()
instrumentor.instrument_app(app)


@app.route('/')
def return_hello():
    player = get_player('OTel Test')
    return 'Hello! Be sure to roll the dice at /rolldice'


@app.route("/rolldice")
def roll_dice():
    player = get_player()
    result = str(roll())
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



def roll():
    return [randint(1, 6), randint(1, 6)]


if __name__ == "__main__":
    serve(TransLogger(app), host=SERVER_HOST, port=SERVER_PORT)
