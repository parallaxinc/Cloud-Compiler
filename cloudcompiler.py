__author__ = 'Michel'

from flask import Flask
app = Flask(__name__)

app.debug = True

@app.route('/')
def hello_world():
    return 'Hello World! 3'

if __name__ == '__main__':
    app.run(host='0.0.0.0')