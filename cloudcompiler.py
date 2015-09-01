__author__ = 'Michel'

import json
from flask import Flask, Response, request

from SpinCompiler import SpinCompiler
from PropCCompiler import PropCCompiler

app = Flask(__name__)

app.debug = True


# ----------------------------------------------------------------------- Spin --------------------------------
@app.route('/single/spin/<action>', methods=['POST'])
def single_spin(action):
    source_files = {
        "single.spin": request.data
    }
    return handle_spin(action, source_files, "single.spin")


@app.route('/multiple/spin/<action>', methods=['POST'])
def multiple_spin(action):
    main_file = request.form.get("main_file", None)
    files = {}
    for file_name in request.files.keys():
        files[file_name] = request.files.get(file_name)
    return handle_spin(action, files, main_file)


def handle_spin(action, source_files, app_filename):
    # format data
    action = action.upper()

    # check data
    if action not in actions:
        failure_data = {
            "success": False,
            "message": "unknown-action",
            "data": action
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")

    # check filename
    if app_filename is None:
        failure_data = {
            "success": False,
            "message": "missing-main-filename"
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")
    if app_filename not in source_files:
        failure_data = {
            "success": False,
            "message": "missing-main-file",
            "data": app_filename
        }
        return Response(json.dumps(failure_data), 200, mimetype="application/json")

    # call compiler and prepare return data
    (success, base64binary, out, err) = compilers["SPIN"].compile(action, source_files, app_filename)
    data = {
        "success": success,
       # "request": source_files,
        "compiler-output": out,
        "compiler-error": err
    }
    if action != "COMPILE" and success:
        data['binary'] = base64binary
    return Response(json.dumps(data), 200, mimetype="application/json")


# ----------------------------------------------------------------------- Propeller C --------------------------------
@app.route('/single/prop-c/<action>', methods=['POST'])
def single_c(action):
    source_files = {
        "single.c": request.data
    }
    return handle_c(action, source_files, "single.c")


@app.route('/multiple/prop-c/<action>', methods=['POST'])
def multiple_c(action):
    return handle_c(action, {}, "test.spin")


def handle_c(action, source_files, app_filename):
    # format data
    action = action.upper()

    # check data
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
    (success, base64binary, out, err) = compilers["PROP-C"].compile(action, source_files, app_filename)
    data = {
        "success": success,
        "compiler-output": out,
        "compiler-error": err
    }
    if action != "COMPILE" and success:
        data['binary'] = base64binary
    return Response(json.dumps(data), 200, mimetype="application/json")

compilers = {
    "SPIN": SpinCompiler(),
    "PROP-C": PropCCompiler()
}

actions = ["COMPILE", "BIN", "EEPROM"]

if __name__ == '__main__':
    app.run(host='0.0.0.0')
