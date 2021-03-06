#  Copyright (c) 2019 Parallax Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining
#  a copy of this software and associated documentation files (the
#  “Software”), to deal in the Software without restriction, including
#  without limitation the rights to use, copy,  modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject
#  to the following conditions:
#
#       The above copyright notice and this permission notice shall be
#       included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#

# from ConfigParser import ConfigParser

import json
import base64
import sys
import logging
from logging import StreamHandler

from flask import Flask, Response, request
from flask_cors import CORS

from SpinCompiler import SpinCompiler
from PropCCompiler import PropCCompiler
from version import version

__author__ = 'Michel'


# Set up basic logging
logging.basicConfig(
    filename='/var/log/supervisor/example.log',
    level=logging.DEBUG,
    format='%(asctime)s $(levelname)s %(name)s %(threadName)s : $(message)s')

app = Flask(__name__)

# Enable CORS
CORS(app)

# ----------------------------------------------------------------------- Spin --------------------------------

# Ping the REST server for signs of life
@app.route('/ping', methods=['GET'])
def ping():
    app.logger.debug('API: ping')
    return Response(
        "{\"result\": \"pong\"}",
        200,
        mimetype="application/json")


@app.route('/version', methods=['GET'])
def get_version():
    app.logger.info('API: version')

    if app.env == 'development':
        data = {
            "success": True,
            "result": "Debugger enabled, library version is not available"
        }
        return Response(json.dumps(data), 500, mimetype="application/json")

    # Get version from version.txt file
    file = open("/opt/parallax/simple-libraries/version.txt", "r")

    if file.mode == 'r':
        lib_version = file.read()

        data = {
            "success": True,
            "simpleLibraryVersion": lib_version.strip(),
            "applicationVersion": version
        }

        return Response(json.dumps(data), 200, mimetype="application/json")
    else:
        return Response(
            "{\"result\": \"fail\"}",
            400,
            mimetype="application/json")


@app.route('/single/spin/<action>', methods=['POST'])
def single_spin(action):
    app.logger.info("API: SingleSpin")
    source_files = {
        "single.spin": request.data
    }
    return handle_spin(action, source_files, "single.spin")


@app.route('/multiple/spin/<action>', methods=['POST'])
def multiple_spin(action):
    app.logger.info("API: MultiSpin")
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
        return Response(json.dumps(failure_data), 400, mimetype="application/json")

    # check filename
    if app_filename is None:
        failure_data = {
            "success": False,
            "message": "missing-main-filename"
        }
        return Response(json.dumps(failure_data), 400, mimetype="application/json")
    if app_filename not in source_files:
        failure_data = {
            "success": False,
            "message": "missing-main-file",
            "data": app_filename
        }
        return Response(json.dumps(failure_data), 400, mimetype="application/json")

    # call compiler and prepare return data
    (success, base64binary, extension, out, err) = compilers["SPIN"].compile(action, source_files, app_filename)

    if err is None:
        err = ''

    data = {
        "success": success,
        "compiler-output": out,
        "compiler-error": err
    }
    if action != "COMPILE" and success:
        data['binary'] = base64binary
        data['extension'] = extension
    return Response(json.dumps(data), 200, mimetype="application/json")


# ---------------------------------------------------------------- Propeller C --------------------------------
@app.route('/single/prop-c/<action>', methods=['POST'])
def single_c(action):
    app.logger.info("API: SinglePropC")

    src = request.data
    source = ""

    if len(src) > 0:
        if not (not isinstance(src, bytes) and not isinstance(src, bytearray)):
            source = src.decode("utf-8")
        else:
            source = src
    else:
        src = request.form.get('code')
        if len(src) > 0:
            if isinstance(src, bytes):
                source = src.decode("utf-8")
            else:
                source = src

    source_files = {
        "single.c": source
    }

    return handle_c(action, source_files, "single.c")


@app.route('/multiple/prop-c/<action>', methods=['POST'])
def multiple_c(action):
    app.logger.info("API: MultiPropC")
    main_file = request.form.get("main_file", None)
    files = {}
    for file_name in request.files.keys():
        files[file_name] = request.files.get(file_name)
    return handle_c(action, files, main_file)


def handle_c(action, source_files, app_filename):
    # format to upper case to make string compares easier
    action = action.upper()

    # Verify that we have received a valid action (COMPILE, BIN, EEPROM)
    if action not in actions:
        failure_data = {
            "success": False,
            "message": "unknown-action",
            "data": action
        }
        return Response(json.dumps(failure_data), 400, mimetype="application/json")

    # check filename
    if app_filename is None:
        failure_data = {
            "success": False,
            "message": "missing-main-filename"
        }
        return Response(json.dumps(failure_data), 400, mimetype="application/json")

    # Is the application file name in the list of files
    if app_filename not in source_files:
        failure_data = {
            "success": False,
            "message": "missing-main-file",
            "data": app_filename
        }
        return Response(json.dumps(failure_data), 400, mimetype="application/json")

    # --------------------------------------------------------------
    # Custom hook to trap the S3 Scribbler demo/initialization block
    # Look for a specific string in the source file (single.c)
    # --------------------------------------------------------------
    if '#pragma load_default_scribbler_binary' in source_files['single.c']:
        app.logger.info("Invoking Scribbler Init library download")

        data = {
            "success": True,
            "compiler-output": "Loading S3 Demo App...",
            "compiler-error": ''
        }

        if action != "COMPILE":
            app.logger.info("Sending Scribbler Init library")
            data['binary'] = s3_load_init_binary().decode('utf-8')
            data['extension'] = 'elf'

        return Response(json.dumps(data), 200, mimetype="application/json")

    app.logger.info("Compiling %s for type %s", app_filename, action)

    # call compiler and prepare return data
    (success, base64binary, extension, out, err) = compilers["PROP-C"].compile(action, source_files, app_filename)

    app.logger.info("Results: %s", out.replace('\n', ' : '))

    if err is None:
        err = ''

    if success:
        # Success! Keep it simple
        out = 'Succeeded.'
    else:
        # Failed! Show the details
        out = 'Failed!\n\n-------- compiler messages --------\n' + out

    data = {
        "success": success,
        "compiler-output": out,
        "compiler-error": err.decode()
    }

    if action != "COMPILE" and success:
        data['binary'] = base64binary.decode('utf-8')
        data['extension'] = extension

    for k, v in data.items():
        app.logger.debug("Data key: %s. Data type: %s", k, type(data[k]))

    resp = Response(json.dumps(data), 200, mimetype="application/json")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


def s3_load_init_binary():
    with open('scribbler_default.binary', 'rb') as f:
        # Encode the binary file contents to base64 byte array
        encoded = base64.b64encode(f.read())

    f.close()

    # Return a string representation of the byte array
    return encoded


# ---------- Defaults and compiler initialization ----------
defaults = {
    'c-compiler': '/opt/parallax/bin/propeller-elf-gcc',
    'c-libraries': '/opt/parallax/simple-libraries',
    'spin-compiler': '/opt/parallax/bin/openspin',
    'spin-libraries': '/opt/parallax/spin'
}

app_configs = defaults

compilers = {
    "SPIN": SpinCompiler(app_configs),
    "PROP-C": PropCCompiler(app_configs)
}

actions = ["COMPILE", "BIN", "EEPROM"]

# -----------------     Logging     --------------------
app.logger.info("DEBUG: %s", app.debug)

if not app.debug:
    handler = StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(threadName)s:%(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)

# --------------     Development server     --------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
