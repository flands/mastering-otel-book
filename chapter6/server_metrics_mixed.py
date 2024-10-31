from random import randint
from flask import Flask, request
from paste.translogger import TransLogger
from waitress import serve
import logging
import os

from opentelemetry.instrumentation.wsgi import collect_request_attributes
from opentelemetry.metrics import get_meter

SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
SERVER_PORT = os.getenv('SERVER_PORT', 8080)

app = Flask(__name__)
appname = os.path.splitext(os.path.basename(__file__))[0]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    player = get_player('OTel User')
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
