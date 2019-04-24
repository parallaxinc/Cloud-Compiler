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

import base64

import os
import subprocess
import shutil
from tempfile import NamedTemporaryFile, mkdtemp
from werkzeug.datastructures import FileStorage

__author__ = 'Michel'


class SpinCompiler:

    def __init__(self, configs):
        self.configs = configs

        self.compile_actions = {
            "COMPILE": {"compile-options": ["-b"], "extension":".binary", "return-binary": False},
            "BIN": {"compile-options": ["-b"], "extension":".binary", "return-binary": True},
            "EEPROM": {"compile-options": ["-e"], "extension":".eeprom", "return-binary": True}
        }

    def compile(self, action, source_files, app_filename):
        spin_source_directory = mkdtemp()
        binary_file = NamedTemporaryFile(suffix=self.compile_actions[action]["extension"], delete=False)
        binary_file.close()

        for filename in source_files:
            with open(spin_source_directory + "/" + filename, mode='w') as source_file:
                if isinstance(source_files[filename], str):
                    source_file.write(source_files[filename])
                elif isinstance(source_files[filename], FileStorage):
                    source_file.write(source_files[filename].stream.read())

        executable = self.configs['spin-compiler']
        lib_directory = self.configs['spin-libraries']

        executing_data = [executable, "-o", binary_file.name, "-L", lib_directory]
        executing_data.extend(self.compile_actions[action]["compile-options"])
        executing_data.append(spin_source_directory + "/" + app_filename)

        process = subprocess.Popen(executing_data, stdout=subprocess.PIPE)

        out, err = process.communicate()

        if process.returncode == 0:
            success = True
        else:
            success = False

        shutil.rmtree(spin_source_directory)

        base64binary = ''

        if self.compile_actions[action]["return-binary"]:
            with open(binary_file.name) as bf:
                base64binary = base64.b64encode(bf.read())

        os.remove(binary_file.name)

        return success, base64binary, self.compile_actions[action]['extension'], out, err
