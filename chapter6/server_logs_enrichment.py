from random import randint
from flask import Flask, request
from paste.translogger import TransLogger
from waitress import serve
import logging
import os

# Log-specific OTel modules
# Note the underscore means the component is currently in development
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

# Signal-agnostic OTel modules
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

# One-time OTel log configuration
exporter = OTLPLogExporter()
resource = get_aggregated_resources(
    [ProcessResourceDetector()],
    Resource.create({"service.name": appname}),
)
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

# Attach OTLP handler to root logger
logging.getLogger().addHandler(handler)


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
