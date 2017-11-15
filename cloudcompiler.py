from ConfigParser import ConfigParser

import json
from flask import Flask, Response, request
from os.path import expanduser, isfile

from SpinCompiler import SpinCompiler
from PropCCompiler import PropCCompiler
import base64

__author__ = 'Michel'

version = "1.0.1"
app = Flask(__name__)


# ------------------------------------- Util functions and classes -------------------------------------------
class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sec_head = '[section]\n'

    def readline(self):
        if self.sec_head:
            try:
                return self.sec_head
            finally:
                self.sec_head = None
        else:
            return self.fp.readline()


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
    source_files = {
        "single.c": request.data
    }
    return handle_c(action, source_files, "single.c")


@app.route('/multiple/prop-c/<action>', methods=['POST'])
def multiple_c(action):
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
        out = "Loading S3 Demo App..."
        data = {
            "success": True,
            "compiler-output": out,
            "compiler-error": ''
        }

        if action != "COMPILE":
            data['binary'] = s3_load_init_binary()
            data['extension'] = 'elf'

        return Response(json.dumps(data), 200, mimetype="application/json")

    # call compiler and prepare return data
    (success, base64binary, extension, out, err) = compilers["PROP-C"].compile(action, source_files, app_filename)

    if err is None:
        err = ''

    if success:
        # Success! Keep it simple
        out = 'Compiled successfully'
    else:
        # Failed! Let's show the details
        out = 'Failed to compile:\n\n' + out

    data = {
        "success": success,
        "compiler-output": out,
        "compiler-error": err
    }

    if action != "COMPILE" and success:
        data['binary'] = base64binary
        data['extension'] = extension

    return Response(json.dumps(data), 200, mimetype="application/json")


def s3_load_init_binary():
    with open('scribbler_default.binary', 'rb') as f:
        encoded = base64.b64encode(f.read())

    f.close()
    return encoded


# --------------------------------------- Defaults and compiler initialization --------------------------------
defaults = {
    'c-compiler': '/opt/parallax/bin/propeller-elf-gcc',
    'c-libraries': '/opt/simple-libraries',
    'spin-compiler': '/opt/parallax/bin/openspin',
    'spin-libraries': '/opt/parallax/spin'
}

configfile = expanduser("~/cloudcompiler.properties")

if isfile(configfile):
    configs = ConfigParser(defaults)
    configs.readfp(FakeSecHead(open(configfile)))

    app_configs = {}
    for (key, value) in configs.items('section'):
        app_configs[key] = value
else:
    app_configs = defaults

compilers = {
    "SPIN": SpinCompiler(app_configs),
    "PROP-C": PropCCompiler(app_configs)
}

actions = ["COMPILE", "BIN", "EEPROM"]


# -------------------------------------------- Logging ---------------------------------------------------------
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('cloudcompiler.log')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)


# ----------------------------------------------- Development server -------------------------------------------
if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0')


