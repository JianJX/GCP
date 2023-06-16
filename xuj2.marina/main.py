from google.cloud import datastore
from flask import Flask, request
import json

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to /boats or /slips to use this API"\

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        content = request.get_json()
        if "name" not in content or "type" not in content or "length" not in content:
            error_response = {}
            error_response["Error"] = "The request object is missing at least one of the required attributes"
            return (error_response, 400)
        new_boat = datastore.entity.Entity(key=client.key("boats"))
        new_boat.update({"name": content["name"], "type": content["type"],
          "length": content["length"]})
        client.put(new_boat)
        content["id"] = new_boat.key.id
        return (content, 201)
    elif request.method == 'GET':
        query = client.query(kind="boats")
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
        return json.dumps(results)
    else:
        return 'Method not recognized'

@app.route('/boats/<id>', methods=['PUT','DELETE','GET', 'PATCH'])
def boats_put_delete(id):
    if request.method == 'PUT':
        content = request.get_json()
        boat_key = client.key("boats", int(id))
        boat = client.get(key=boat_key)
        if boat == None:
            error_response = {}
            error_response["Error"] = "No boat with this boat_id exists"
            return (error_response, 404)
        if "name" not in content or "type" not in content or "length" not in content:
            error_response = {}
            error_response["Error"] = "The request object is missing at least one of the required attributes"
            return (error_response, 400)
        boat.update({"name": content["name"], "type": content["type"], "length": content["length"]})
        client.put(boat)
        response_body = {}
        response_body["id"] = int(id)
        response_body["name"] = boat["name"]
        response_body["type"] = boat["type"]
        response_body["length"] = boat["length"]
        return (response_body, 200)
    elif request.method == 'DELETE':
        query = client.query(kind="boats")
        results = list(query.fetch())
        for e in results:
            if e.key.id == int(id):
                key = client.key("boats", int(id))
                client.delete(key)
                query = client.query(kind="slips")
                results = list(query.fetch())
                for e in results:
                    if e["current_boat"] == int(id):
                        slip_key = client.key("slips", e.key.id)
                        slip = client.get(key=slip_key)
                        slip.update({"current_boat": None})
                        client.put(slip)
                return ("", 204)
        error_response = {}
        error_response["Error"] = "No boat with this boat_id exists"
        return (error_response, 404)
    elif request.method == 'GET':
        boat_key = client.key("boats", int(id))
        boat = client.get(key=boat_key)
        if boat == None:
            error_response = {}
            error_response["Error"] = "No boat with this boat_id exists"
            return (error_response, 404)
        else:
            response_body = {}
            response_body["id"] = int(id)
            response_body["name"] = boat["name"]
            response_body["type"] = boat["type"]
            response_body["length"] = boat["length"]
            return (response_body, 200)
    elif request.method == 'PATCH':
        content = request.get_json()
        boat_key = client.key("boats", int(id))
        boat = client.get(key=boat_key)
        if boat == None:
            error_response = {}
            error_response["Error"] = "No boat with this boat_id exists"
            return (error_response, 404)
        if "name" not in content or "type" not in content or "length" not in content:
            error_response = {}
            error_response["Error"] = "The request object is missing at least one of the required attributes"
            return (error_response, 400)
        boat.update({"name": content["name"], "type": content["type"], "length": content["length"]})
        client.put(boat)
        response_body = {}
        response_body["id"] = int(id)
        response_body["name"] = boat["name"]
        response_body["type"] = boat["type"]
        response_body["length"] = boat["length"]
        return (response_body, 200)
    else:
        return 'Method not recognized'

@app.route('/slips', methods=['POST','GET'])
def slips_get_post():
    if request.method == 'POST':
        content = request.get_json()
        if "number" not in content:
            error_response = {}
            error_response["Error"] = "The request object is missing the required number"
            return (error_response, 400)
        new_slip = datastore.entity.Entity(key=client.key("slips"))
        new_slip.update({"number": content["number"], "current_boat": None})
        client.put(new_slip)
        content["id"] = new_slip.key.id
        content["current_boat"] = None
        return (content, 201)
    elif request.method == 'GET':
        query = client.query(kind="slips")
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
        return json.dumps(results)
    else:
        return 'Method not recognized'

@app.route('/slips/<id>', methods=['DELETE','GET'])
def slips_delete_get(id):
    if request.method == 'DELETE':
        query = client.query(kind="slips")
        results = list(query.fetch())
        for e in results:
            if e.key.id == int(id):
                key = client.key("slips", int(id))
                client.delete(key)
                return ("", 204)
        error_response = {}
        error_response["Error"] = "No slip with this slip_id exists"
        return (error_response, 404)
    elif request.method == 'GET':
        slip_key = client.key("slips", int(id))
        slip = client.get(key=slip_key)
        if slip == None:
            error_response = {}
            error_response["Error"] = "No slip with this slip_id exists"
            return (error_response, 404)
        else:
            response_body = {}
            response_body["id"] = int(id)
            response_body["number"] = slip["number"]
            response_body["current_boat"] = slip["current_boat"]
            return (response_body, 200)
    else:
        return 'Method not recognized'

@app.route('/slips/<slip_id>/<boat_id>', methods=['PUT', 'DELETE'])
def boat_arrives_or_departs_slip(slip_id, boat_id):
    if request.method == 'PUT':
        slip_key = client.key("slips", int(slip_id))
        slip = client.get(key=slip_key)
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        if slip == None or boat == None:
            error_response = {}
            error_response["Error"] = "The specified boat and/or slip does not exist"
            return (error_response, 404)
        if slip["current_boat"] != None:
            error_response = {}
            error_response["Error"] = "The slip is not empty"
            return (error_response, 403)
        slip.update({"current_boat": int(boat_id)})
        client.put(slip)
        return ("", 204)
    elif request.method == 'DELETE':
        slip_key = client.key("slips", int(slip_id))
        slip = client.get(key=slip_key)
        boat_key = client.key("boats", int(boat_id))
        boat = client.get(key=boat_key)
        error_response = {}
        error_response["Error"] = "No boat with this boat_id is at the slip with this slip_id"
        if slip == None or boat == None or slip["current_boat"] == None:
            return (error_response, 404)
        if slip["current_boat"] != int(boat_id):
            return (error_response, 404)
        slip.update({"current_boat": None})
        client.put(slip)
        return ("", 204)
    else:
        return 'Method not recognized'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)