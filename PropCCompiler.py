import base64
import shutil

__author__ = 'Michel'

import os
import json
import subprocess
import re
from tempfile import NamedTemporaryFile, mkdtemp


class PropCCompiler:

    def __init__(self):
        self.compiler_executable = "/opt/parallax/bin/propeller-elf-gcc"

        self.compile_actions = {
            "COMPILE": {"compile-options": [], "extension":".elf", "return-binary": False},
            "BIN": {"compile-options": [], "extension":".elf", "return-binary": True},
            "EEPROM": {"compile-options": [], "extension":".elf", "return-binary": True}
        }

        self.appdir = os.getcwd()

    def compile(self, action, source_files, app_filename):
        c_source_directory = mkdtemp()
        binary_file = NamedTemporaryFile(suffix=self.compile_actions[action]["extension"], delete=False)
        binary_file.close()

        for filename in source_files:
            with open(c_source_directory + "/" + filename, mode='w') as source_file:
                source_file.write(source_files[filename])

        includes = self.parse_includes(source_files)  # parse includes
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

        shutil.rmtree(c_source_directory)

        base64binary = ''

        if self.compile_actions[action]["return-binary"]:
            with open(binary_file.name) as bf:
                base64binary = base64.b32encode(bf.read())

        os.remove(binary_file.name)

        return (success, base64binary, out, err)

    def get_includes(self, includes):
        lib_descriptor = json.load(open(self.appdir + "/propeller-c-lib/lib-descriptor.json"))

        descriptors = []
        for include in includes:
            for descriptor in lib_descriptor:
                if include in descriptor['include']:
                    descriptors.append(descriptor)
        return descriptors

    def parse_includes(self, source_files):
        includes = set()

        for file_name in source_files:
            c_file = source_files[file_name]
            for line in c_file.splitlines():
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
