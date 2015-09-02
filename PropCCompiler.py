import base64
import shutil
from werkzeug.datastructures import FileStorage

import os
import json
import subprocess
import re
from tempfile import NamedTemporaryFile, mkdtemp

__author__ = 'Michel'


class PropCCompiler:

    def __init__(self):
        self.compiler_executable = "/opt/parallax/bin/propeller-elf-gcc"

        self.compile_actions = {
            "COMPILE": {"compile-options": [], "extension":".elf", "return-binary": False},
            "BIN": {"compile-options": [], "extension":".elf", "return-binary": True},
            "EEPROM": {"compile-options": [], "extension":".elf", "return-binary": True}
        }

        self.lib_descriptor = json.load(open(self.appdir + "/propeller-c-lib/lib-descriptor.json"))

        #self.appdir = os.getcwd()

    def compile(self, action, source_files, app_filename):
        c_source_directory = mkdtemp()

        c_file_data = {}
        h_file_data = {}

        # Write all files to working directory
        for filename in source_files:
            if filename.endswith(".h"):
                with open(c_source_directory + "/" + filename, mode='w') as header_file:
                    if isinstance(source_files[filename], basestring):
                        file_content = source_files[filename]
                    elif isinstance(source_files[filename], FileStorage):
                        file_content = source_files[filename].stream.read()

                    header_file.write(file_content)

        for filename in source_files:
            if filename.endswith(".c"):
                with open(c_source_directory + "/" + filename, mode='w') as source_file:
                    if isinstance(source_files[filename], basestring):
                        file_content = source_files[filename]
                    elif isinstance(source_files[filename], FileStorage):
                        file_content = source_files[filename].stream.read()

                    source_file.write(file_content)

                c_file_data[filename] = self.parse_includes(file_content)
            elif filename.endswith(".h"):
                h_file_data[filename] = {}

        # determine order
        # Precompile libraries

        shutil.rmtree(c_source_directory)


    def compile_lib(self, source_file, app_filename, libraries):
        pass

    def compile_binary(self, action, c_source_directory, source_file_code, app_filename, libraries):
        binary_file = NamedTemporaryFile(suffix=self.compile_actions[action]["extension"], delete=False)
        binary_file.close()

        for library in libraries:
            pass

        includes = self.parse_includes(source_file_code)  # parse includes
        descriptors = self.get_includes(includes)  # get lib descriptors for includes
        executing_data = self.create_executing_data(c_source_directory + "/" + app_filename, binary_file, descriptors)  # build execution command

        try:
            process = subprocess.Popen(executing_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # call compile

            out, err = process.communicate()

            if process.returncode == 0 and (err is None or len(err) == 0):
                out = "Compile successful\n"
                success = True
            else:
                success = False
        except OSError:
            out = ""
            err = "Compiler not found\n"
            success = False

        base64binary = ''

        if self.compile_actions[action]["return-binary"]:
            with open(binary_file.name) as bf:
                base64binary = base64.b32encode(bf.read())

        os.remove(binary_file.name)

        return (success, base64binary, out, err)

    def get_includes(self, includes):


        descriptors = []
        for include in includes:
            # First: look into files

            # If not found: look in libraries
            for descriptor in self.lib_descriptor:
                if include in descriptor['include']:
                    descriptors.append(descriptor)
        return descriptors

    def parse_includes(self, source_file):
        includes = set()

        for line in source_file.splitlines():
            if '#include' in line:
                match = re.match(r'^#include "(\w+).h"', line)
                if match:
                    includes.add(match.group(1))

        return includes

    def create_executing_data(self, main_c_file_name, binary_file, descriptors):
        executable = self.compiler_executable

        lib_directory = self.appdir + "/propeller-c-lib/"

        executing_data = [executable]
        for descriptor in descriptors:
            executing_data.append("-I")
            executing_data.append(lib_directory + descriptor["libdir"])
            executing_data.append("-L")
            executing_data.append(lib_directory + descriptor["memorymodel"]["cmm"])
        executing_data.append("-Os")
        executing_data.append("-mcmm")
        executing_data.append("-m32bit-doubles")
        executing_data.append("-std=c99")
        executing_data.append("-o")
        executing_data.append(binary_file.name)
        executing_data.append(main_c_file_name)
        executing_data.append("-lm")
        while len(descriptors) > 0:
            for descriptor in descriptors:
                executing_data.append("-l" + descriptor["name"])
            executing_data.append("-lm")
            del descriptors[-1]

        return executing_data
