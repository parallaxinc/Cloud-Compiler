#  Copyright (c) 2022 Parallax Inc.
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
import shutil
from werkzeug.datastructures import FileStorage
import os
import subprocess
import re

from tempfile import NamedTemporaryFile, mkdtemp
import cloudcompiler


class PropCCompiler:

    def __init__(self, configs):
        self.configs = configs

        self.compile_actions = {
            "COMPILE": {"compile-options": [], "extension": ".elf", "return-binary": False},
            "BIN": {"compile-options": [], "extension": ".elf", "return-binary": True},
            "EEPROM": {"compile-options": [], "extension": ".elf", "return-binary": True}
        }

    def compile(self, action: str, source_files: dict, app_filename: str):
        source_directory = mkdtemp()

        c_file_data = {}
        h_file_data = {}

        # Write all files to working directory
        # Header files
        for filename in source_files:
            if filename.endswith(".h"):
                with open(source_directory + "/" + filename, mode='w', encoding='utf-8') as header_file:
                    if isinstance(source_files[filename], str):
                        file_content = source_files[filename]
                    elif isinstance(source_files[filename], FileStorage):
                        file_content = source_files[filename].stream.read()

                    header_file.write(file_content)

                # Check c file exists
                c_filename = filename[:-1] + 'c'
                if c_filename not in source_files:
                    return False, None, '', '', 'Missing c file %s for header %s' % (c_filename, filename)

                h_file_data[filename] = {
                    'c_filename': c_filename
                }

        # C source files
        # Loop through the array of sources in the source_files array and write
        # their contents to physical files that the compiler can see.
        for filename in source_files:
            if filename.endswith(".c"):
                with open(source_directory + "/" + filename, mode='w', encoding='utf-8') as source_file:

                    cloudcompiler.app.logger.debug(
                        "Source file is of type: %s",
                        type(source_files[filename]))

                    if isinstance(source_files[filename], str):
                        file_content = source_files[filename]

                    elif isinstance(source_files[filename], bytes):
                        file_content = source_files[filename].decode()

                    elif isinstance(source_files[filename], FileStorage):
                        file_content = source_files[filename].stream.read()

                    source_file.write(file_content)

                c_file_data[filename] = {
                    'includes': self.parse_includes(file_content)
                }

                # Check header file exists
                h_filename = filename[:-1] + 'h'
                c_file_data[filename]['library'] = h_filename in source_files

        compiler_output = ''
        library_order = []
        external_libraries = []

        # determine order and direct library dependencies
        for include in c_file_data[app_filename]['includes']:
            self.determine_order(include, library_order, external_libraries, h_file_data, c_file_data)

        # determine library dependencies
        external_libraries_info = {}
        for library in external_libraries:
            self.find_dependencies(library, external_libraries_info)

        if len(external_libraries) > 0:
            compiler_output += "Included libraries: %s\n" % ', '.join(external_libraries)

        # TODO determine if the following statement and executing_data need adjusting when
        #  multi-file projects are enabled

        if len(library_order) > 0:
            compiler_output += "Library compile order: %s\n" % ', '.join(library_order)

        success = True
        # Precompile libraries
        for library in library_order:
            compiler_output += "Compiling: %s\n" % library
            (lib_success, lib_out, lib_err) = self.compile_lib(
                source_directory,
                library + '.c',
                library + '.o',
                external_libraries_info)

            if lib_success:
                compiler_output += lib_out + '\n'
            else:
                compiler_output += lib_err + '\n'
                success = False

        base64binary = None
        err = None

        if success:
            cloudcompiler.app.logger.debug("Source directory: %s", source_directory)
            cloudcompiler.app.logger.debug("Action          : %s", action)
            cloudcompiler.app.logger.debug("App File Name   : %s", app_filename)
            cloudcompiler.app.logger.debug("Library order   : %s", library_order)
            cloudcompiler.app.logger.debug("External libs   : %s", external_libraries_info)

            # Compile binary
            (bin_success, base64binary, out, err) = self.compile_binary(
                source_directory,
                action,
                app_filename,
                library_order,
                external_libraries_info)

            # The data type of out appears to be either a string
            # or an array of bytes.
            if isinstance(out, str):
                compiler_output += out
            else:
                compiler_output += out.decode()

            if not bin_success:
                success = False

        shutil.rmtree(source_directory)

        return success, base64binary, self.compile_actions[action]["extension"], compiler_output, err

    def determine_order(self, header_file, library_order, external_libraries, header_files, c_files):
        if header_file not in library_order:

            # TODO review to check what happens if no header supplied (if that is valid)

            if header_file + '.h' in header_files:
                includes = c_files[header_files[header_file + '.h']['c_filename']]['includes']
                for include in includes:
                    self.determine_order(include, library_order, external_libraries, header_files, c_files)
                library_order.append(header_file)
            else:
                if header_file not in external_libraries:
                    external_libraries.append(header_file)

    def find_dependencies(self, library: str, libraries: dict):
        library_present = False

        # ---------------------------------------------------------------------
        # Walk through the c-libraries directory tree, looking for .h files
        # and compare the found file names with the list of header files that
        # are defined in the libraries list
        #
        # This process can take some time. A trivial source file with 2 or
        # three header files can consume 200ms in this loop.
        # ---------------------------------------------------------------------
        for root, subFolders, files in os.walk(self.configs['c-libraries']):
            if library + '.h' in files:
                if library in root[root.rindex('/') + 1:]:
                    library_present = True
                    if library + '.c' in files:
                        with open(root + '/' + library + '.c', encoding="latin-1") as library_code:
                            cloudcompiler.app.logger.debug("Parsing '%s'", root + '/' + library + '.c')
                            includes = self.parse_includes(library_code.read())
                    else:
                        with open(root + '/' + library + '.h', encoding="latin-1") as header_code:
                            cloudcompiler.app.logger.debug("Parsing '%s'", root + '/' + library + '.h')
                            includes = self.parse_includes(header_code.read())

                    libraries[library] = {
                        'path': root
                    }

                    for include in includes:
                        if include not in libraries:
                            (success, logging) = self.find_dependencies(include, libraries)
                            if not success:
                                return success, logging
                else:
                    return True, ''

        if library_present:
            return True, ''
        else:
            return False, 'Library %s not found' % library

    def compile_lib(self, working_directory: str, source_file: str, target_filename: str, libraries: dict):
        cloudcompiler.app.logger.info("Working directory: %s", working_directory)
        cloudcompiler.app.logger.info("Compiling source file: %s to target file: %s", source_file, target_filename)

        # build execution command
        executing_data = self.create_lib_executing_data(source_file, target_filename, libraries)

        # print(' '.join(executing_data), file=sys.stderr)

        try:
            # call compile
            process = subprocess.Popen(
                executing_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_directory)

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

        return success, out, err

    def compile_binary(self, working_directory, action, source_file, binaries, libraries):
        binary_file = NamedTemporaryFile(suffix=self.compile_actions[action]["extension"], delete=False)

        binary_file.close()

        # build execution command
        executing_data = self.create_executing_data(source_file, binary_file.name, binaries, libraries)
        # print(' '.join(executing_data))

        try:
            process = subprocess.Popen(
                executing_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_directory)  # call compile

            out, err = process.communicate()

            if process.returncode == 0:  # and (err is None or len(err) == 0):
                out = "Compile successful\n"
                success = True
            else:
                success = False
        except OSError:
            out = ""
            err = "Compiler not found\n"
            success = False

        base64binary = ''

        if success and self.compile_actions[action]["return-binary"]:
            with open(binary_file.name, mode='rb') as bf:
                base64binary = base64.b64encode(bf.read())

        if success:
            os.remove(binary_file.name)

        return success, base64binary, out, err

    def parse_includes(self, source_file):
        includes = set()

        for line in source_file.splitlines():
            if '#include' in line:
                match = re.match(r'^#include "(\w+).h"', line)
                if match:
                    includes.add(match.group(1))

        return includes

    def create_lib_executing_data(self, lib_c_file_name: str, binary_file: str, descriptors):
        executable = self.configs['c-compiler']

        executing_data = [executable, "-I", ".", "-L", "."]

        for descriptor in descriptors:
            executing_data.append("-I")
            executing_data.append(descriptors[descriptor]["path"])
            executing_data.append("-L")
            executing_data.append(descriptors[descriptor]["path"] + '/cmm')

        executing_data.append("-Os")
        executing_data.append("-mcmm")
        executing_data.append("-m32bit-doubles")
        executing_data.append("-std=c99")
        executing_data.append("-c")
        executing_data.append(lib_c_file_name)
        executing_data.append("-o")
        executing_data.append(binary_file)

        return executing_data

    def create_executing_data(self, main_c_file_name: str, binary_file: str, binaries: dict, descriptors: dict):
        executable = self.configs['c-compiler']

        executing_data = [executable, "-I", ".", "-L", "."]

        for descriptor in descriptors:
            executing_data.append("-I")
            executing_data.append(descriptors[descriptor]["path"])
            executing_data.append("-L")
            executing_data.append(descriptors[descriptor]["path"] + '/cmm')

        executing_data.append("-Os")
        executing_data.append("-mcmm")
        executing_data.append("-m32bit-doubles")
        executing_data.append("-std=c99")
        executing_data.append("-o")
        executing_data.append(binary_file)

        for binary in binaries:
            executing_data.append(binary + ".o")

        executing_data.append(main_c_file_name)
        libraries = descriptors.keys()
        executing_data.append("-Wl,--start-group")
        executing_data.append("-lm")

        for library in libraries:
            executing_data.append("-l" + library)

        executing_data.append("-Wl,--end-group")

        return executing_data
