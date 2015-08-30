import base64

__author__ = 'Michel'

import os
import subprocess
from tempfile import NamedTemporaryFile


class SpinCompiler:

    def __init__(self):
        self.compiler_executable = "/compilers/openspin"

        self.compile_actions = {
            "COMPILE": {"compile-options": ["-b"], "extension":".binary", "return-binary": False},
            "RAM": {"compile-options": ["-b"], "extension":".binary", "return-binary": True},
            "EEPROM": {"compile-options": ["-e"], "extension":".eeprom", "return-binary": True}
        }

        self.appdir = os.getcwd()

    def simple_compile(self, action, code):
        spin_file = NamedTemporaryFile(mode='w', suffix='.spin', delete=False)
        binary_file = NamedTemporaryFile(suffix=self.compile_actions[action]["extension"], delete=False)
        spin_file.write(code)
        spin_file.close()
        binary_file.close()

        executable = self.appdir + self.compiler_executable
        print(executable)
        lib_directory = self.appdir + "/propeller-lib"

        executing_data = [executable, "-o", binary_file.name, "-L", lib_directory]
        executing_data.extend(self.compile_actions[action]["compile-options"])
        executing_data.append(spin_file.name)

        process = subprocess.Popen(executing_data, stdout=subprocess.PIPE)

        out, err = process.communicate()

        if process.returncode == 0:
            success = True
        else:
            success = False

        os.remove(spin_file.name)
        if self.compile_actions[action]["return-binary"]:
            with open(binary_file.name) as bf:
                base64binary = base64.b32encode(bf.readall())

        os.remove(binary_file.name)

        return (success, base64binary, out, err)
