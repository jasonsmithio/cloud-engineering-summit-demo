import os
import json
import logging
import time

from flask import Flask, jsonify, redirect, render_template, request, Response

from kafka import KafkaProducer

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers=['my-cluster-kafka-bootstrap.kafka:9092'])


def info(msg):
    app.logger.info(msg)


@app.route('/', methods=['POST'])
def default_route():
    if request.method == 'POST':
        content = request.data.decode('utf-8')
        info(f'Event Display received event: {content}')

        producer.send('finance', bytes(content, encoding='utf-8'))
        return jsonify(hello=str(content))
    else:
        return jsonify('hello world')


if __name__ != '__main__':
    # Redirect Flask logs to Gunicorn logs
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    info('Event Display starting')
else:
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
