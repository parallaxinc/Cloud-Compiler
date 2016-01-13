from locust import HttpLocust, TaskSet, task


single_spin_wait = "PUB Blinky\n  DIRA[16]~~\n  repeat\n    OUTA[16]~\n    waitcnt(clkfreq + cnt)\n    OUTA[16]~~\n    waitcnt(clkfreq + cnt)\n"
single_spin_toggle = "PUB blinky\n  repeat\n    !outa[16]\n"


single_c = '#include "simpletools.h"\nint main() {\n  while(1) {\n    high(16);\n    pause(1000);\n    low(16);\n    pause(1000);\n  }\n}\n'


class CCompilerTaskSet(TaskSet):

    @task
    def single_spin_wait(self):
        self.client.post("/single/spin/compile", data=single_spin_wait)

    @task
    def single_spin_toggle(self):
        self.client.post("/single/spin/compile", data=single_spin_toggle)

    @task
    def single_c(self):
        self.client.post("/single/prop-c/compile", data=single_c)


class CCompilerLocust(HttpLocust):
    task_set = CCompilerTaskSet
    min_wait = 5000
    max_wait = 15000
