from google.cloud import datastore
from flask import Flask, request
import json
import car
import parking
import owner
import auth

app = Flask(__name__)
app.register_blueprint(owner.bp)
app.register_blueprint(car.bp)
app.register_blueprint(parking.bp)
app.register_blueprint(auth.bp)

@app.route('/')
def index():
    return "Please navigate to /cars or /parkings to use this API"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)