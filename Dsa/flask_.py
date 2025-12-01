from flask import Flask

app = Flask(__name__)


@app.route("/")
def welcome():
    return "gp"
if __name__ == "__main__":
    app.run()