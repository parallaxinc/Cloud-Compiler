import base64

__author__ = 'Michel'

import os
import subprocess
import shutil
from tempfile import NamedTemporaryFile, mkdtemp


class SpinCompiler:

    def __init__(self):
        self.compiler_executable = "/compilers/openspin"

        self.compile_actions = {
            "COMPILE": {"compile-options": ["-b"], "extension":".binary", "return-binary": False},
            "RAM": {"compile-options": ["-b"], "extension":".binary", "return-binary": True},
            "EEPROM": {"compile-options": ["-e"], "extension":".eeprom", "return-binary": True}
        }

        self.appdir = os.getcwd()

    def compile(self, action, source_files, app_filename):
        spin_source_directory = mkdtemp()
      #  spin_file = NamedTemporaryFile(mode='w', suffix='.spin', delete=False)
        binary_file = NamedTemporaryFile(suffix=self.compile_actions[action]["extension"], delete=False)
      #  spin_file.write(source_files["single.spin"])
      #  spin_file.close()
        binary_file.close()

        for filename in source_files:
            with open(spin_source_directory + "/" + filename, mode='w') as source_file:
                source_file.write(source_files[filename])

       # print("Spin source directory: " + spin_source_directory)

        executable = self.appdir + self.compiler_executable

        lib_directory = self.appdir + "/propeller-spin-lib"

        executing_data = [executable, "-o", binary_file.name, "-L", lib_directory]
        executing_data.extend(self.compile_actions[action]["compile-options"])
        executing_data.append(spin_source_directory + "/" + app_filename)

        process = subprocess.Popen(executing_data, stdout=subprocess.PIPE)

        out, err = process.communicate()

        if process.returncode == 0:
            success = True
        else:
            success = False

      #  os.remove(spin_file.name)
      #  os.removedirs(spin_source_directory)
        shutil.rmtree(spin_source_directory)

        base64binary = ''

        if self.compile_actions[action]["return-binary"]:
            with open(binary_file.name) as bf:
                base64binary = base64.b32encode(bf.read())

        os.remove(binary_file.name)

        return (success, base64binary, out, err)
