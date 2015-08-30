__author__ = 'Michel'

import json
from flask import Flask, Response, request

from SpinCompiler import SpinCompiler
#from PropCCompiler import PropCCompiler

app = Flask(__name__)

app.debug = True


@app.route('/single/<action>/<language>', methods=['POST'])
def single(action, language):
    source_files = [
        request.data
    ]
    response_data = handle(action, language, source_files)
    return Response(json.dumps(response_data), 200, mimetype="application/json")


@app.route('/multiple/<action>/<language>', methods=['POST'])
def multiple(action, language):
    response_data = handle(action, language, [])
    return Response(json.dumps(response_data), 200, mimetype="application/json")


def handle(action, language, source_files):
    data = {
        "action": action,
        "language": language,
        "request": source_files
    }
    return data

compiler = {
    "spin": SpinCompiler(),
#    "prop-c": PropCCompiler()
}

if __name__ == '__main__':
    app.run(host='0.0.0.0')
