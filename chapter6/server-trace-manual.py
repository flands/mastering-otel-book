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
from opentelemetry.propagate import extract
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.trace import (
    get_current_span,
    get_tracer_provider,
    set_tracer_provider,
    SpanKind,
    Status,
    StatusCode,
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

# One-time trace-specific OTel configuration
# Replace OTLPSpanExporter with ConsoleSpanExporter if not using the Collector
set_tracer_provider(TracerProvider(
    active_span_processor=BatchSpanProcessor(OTLPSpanExporter()),
    resource=resource,
))
tracer = get_tracer_provider().get_tracer(__name__)


@app.route("/")
def return_hello():
    # Signal-agnostic, function-specific OTel attributes creation
    attributes = collect_request_attributes(request.environ)
 
    # Trace-specific OTel span creation
    with tracer.start_as_current_span(
        "server_request",
        context=extract(request.headers),
        kind=SpanKind.SERVER,
        attributes=attributes,
    ):
        player = get_player('OTel Test')
        return "Hello! Be sure to roll the dice at /rolldice"


@app.route("/rolldice")
def roll_dice():    
    # Signal-agnostic, function-specific OTel attributes creation
    attributes = collect_request_attributes(request.environ)

    # Trace-specific OTel span creation
    with tracer.start_as_current_span(
        "roll_dice_request",
        context=extract(request.headers),
        kind=SpanKind.SERVER,
        attributes=attributes,
    ): 
        current_span = get_current_span()
        player = get_player()
        current_span.set_attribute("player", player)

        current_span.add_event("Rolling dice!")
        result = str(roll())
        current_span.add_event("Got a result!", attributes={"result": result})
        logger.warning("%s rolled a: %s", player, result)
        return result


def get_player(default=None):
    try:
        if default is None:
            default = 'Anonymous player'
            raise TypeError
    except TypeError as e:
        get_current_span().record_exception(e)
        logger.warning("Player request arg not set")
    return request.args.get('player', default=default, type=str)


def roll():
    return [randint(1, 6), randint(1, 6)]


if __name__ == "__main__":
    serve(TransLogger(app), host=SERVER_HOST, port=SERVER_PORT)
