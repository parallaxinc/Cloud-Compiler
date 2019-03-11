from locust import HttpLocust, TaskSet, task


single_spin = ("PUB Blinky\n"
               "  DIRA[16]~~\n"
               "  repeat\n"
               "    OUTA[16]~\n"
               "    waitcnt(clkfreq + cnt)\n"
               "    OUTA[16]~~\n"
               "    waitcnt(clkfreq + cnt)\n")

single_c = ('#include "simpletools.h"\n'
            'int main() {\n'
            '  while(1) {\n'
            '    high(16);\n'
            '    pause(1000);\n'
            '    low(16);\n'
            '    pause(1000);\n'
            '  }\n'
            '}\n')


class CCompilerTaskSet(TaskSet):

    @task
    def single_spin_compile(self):
        self.client.post("/single/spin/compile", data=single_spin)

    @task
    def single_spin_bin(self):
        self.client.post("/single/spin/bin", data=single_spin)

    @task
    def single_spin_eeprom(self):
        self.client.post("/single/spin/eeprom", data=single_spin)

    @task
    def single_c_compile(self):
        self.client.post("/single/prop-c/compile", data=single_c)

    @task
    def single_c_bin(self):
        self.client.post("/single/prop-c/bin", data=single_c)

    @task
    def single_c_eeprom(self):
        self.client.post("/single/prop-c/eeprom", data=single_c)


class CCompilerLocust(HttpLocust):
    task_set = CCompilerTaskSet
    min_wait = 5000
    max_wait = 15000
