__author__ = 'Michel'

import json
from flask import Flask, Response, request

from SpinCompiler import SpinCompiler
#from PropCCompiler import PropCCompiler

app = Flask(__name__)

app.debug = True


@app.route('/single/<action>/<language>', methods=['POST'])
def single(action, language):
    language = language.upper()

    # check language so that single app filename can be safely used
    if language not in compiler:
        failure_data = {
            "success": False,
            "message": "unknown-language",
            "data": language
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")

    source_files = {
        compiler[language]["single-app-filename"]: request.data
    }
    return handle(action, language, source_files, compiler[language]["single-app-filename"])


@app.route('/multiple/<action>/<language>', methods=['POST'])
def multiple(action, language):
    return handle(action, language, {}, "test.spin")


def handle(action, language, source_files, app_filename):
    # format data
    action = action.upper()
    language = language.upper()

    # check data
    if language not in compiler:
        failure_data = {
            "success": False,
            "message": "unknown-language",
            "data": language
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")
    if action not in actions:
        failure_data = {
            "success": False,
            "message": "unknown-action",
            "data": action
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")

    # check filename
    if app_filename not in source_files:
        failure_data = {
            "success": False,
            "message": "missing-app-filename",
            "data": app_filename
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")

    # call compiler and prepare return data
    (success, base64binary, out, err) = compiler[language]["compiler"].compile(action, source_files, app_filename)
    data = {
        "success": success,
       # "request": source_files,
        "compiler-output": out,
        "compiler-error": err
    }
    if action != "COMPILE" and success:
        data['binary'] = base64binary
    return Response(json.dumps(data), 200, mimetype="application/json")

compiler = {
    "SPIN": {"compiler": SpinCompiler(), "single-app-filename": "single.spin"},
#    "prop-c": {"compiler": PropCCompiler(), "single-app-filename": "single.c"}
}

actions = ["COMPILE", "RAM", "EEPROM"]

if __name__ == '__main__':
    app.run(host='0.0.0.0')
