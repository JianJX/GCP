from flask import Blueprint, request
from google.cloud import datastore
import json

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        content = request.get_json()
        if "name" not in content or "type" not in content or "length" not in content:
            error_response = {}
            error_response["Error"] = "The request object is missing at least one of the required attributes"
            return (error_response, 400)
        new_boat = datastore.entity.Entity(key=client.key("boats"))
        new_boat.update({'name': content['name'], 'type': content['type'], 
        'length': content['length'], "loads": []})
        client.put(new_boat)
        selfURL = request.base_url + '/' + str(new_boat.key.id)
        #new_boat.update({"self": selfURL})
        #client.put(new_boat)
        content["id"] = new_boat.key.id
        content["loads"] = []
        content["self"] = selfURL
        return (content, 201)
    elif request.method == 'GET':
        query = client.query(kind="boats")
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e.key.id)
        output = {"boats": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)
    else:
        return 'Method not recogonized'

@bp.route('/<id>', methods=['PUT','DELETE'])
def boats_put_delete(id):
    if request.method == 'PUT':
        content = request.get_json()
        boat_key = client.key("boats", int(id))
        boat = client.get(key=boat_key)
        boat.update({"name": content["name"], "type": content["type"],
          "length": content["length"], "loads": content["loads"]})
        client.put(boat)
        return ('',200)
    elif request.method == 'DELETE':
        boat_key = client.key("boats", int(id))
        boat = client.get(key=boat_key)
        if boat == None:
            return ({"Error": "No boat with this boat_id exists"}, 404)
        if boat["loads"] != None:
            for l in boat["loads"]:
                load_key = client.key("loads", l["id"])
                load = client.get(key=load_key)
                load["carrier"] = None
                client.put(load)
        client.delete(boat_key)
        return ('',204)
    else:
        return 'Method not recogonized'

@bp.route('/<bid>/loads/<lid>', methods=['PUT','DELETE'])
def assign_remove_load(bid,lid):
    if request.method == 'PUT':
        boat_key = client.key("boats", int(bid))
        boat = client.get(key=boat_key)
        load_key = client.key("loads", int(lid))
        load = client.get(key=load_key)
        if boat == None or load == None:
            return ({"Error": "The specified boat and/or load does not exist"}, 404)
        if load["carrier"] != None:
            return ({"Error": "The load is already loaded on another boat"}, 403)
        new_load = {"id": load.key.id}
        boat["loads"].append(new_load)
        client.put(boat)
        new_carrier = {"id": boat.key.id}
        load["carrier"] = new_carrier
        client.put(load)
        return('',204)
    if request.method == 'DELETE':
        boat_key = client.key("boats", int(bid))
        boat = client.get(key=boat_key)
        load_key = client.key("loads", int(lid))
        load = client.get(key=load_key)
        if boat == None or load == None:
            return ({"Error": "No boat with this boat_id is loaded with the load with this load_id"}, 404)
        for l in boat["loads"]:
            if l["id"] == load.key.id:
                boat['loads'].remove(l)
                client.put(boat)
                load["carrier"] = None
                client.put(load)
                return('',204)
        return ({"Error": "No boat with this boat_id is loaded with the load with this load_id"}, 404)

@bp.route('/<id>', methods=['GET'])
def boat_get_by_id(id):
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
        for load in boat["loads"]:
            load["self"] = request.host_url + 'loads/' + str(load["id"])
        response_body["loads"] = boat["loads"]
        response_body["self"] = request.base_url
        return (response_body, 200)

@bp.route('/<id>/loads', methods=['GET'])
def get_all_loads(id):
    boat_key = client.key("boats", int(id))
    boat = client.get(key=boat_key)
    if boat == None:
        error_response = {}
        error_response["Error"] = "No boat with this boat_id exists"
        return (error_response, 404)
    else:
        load_list  = []
        if 'loads' in boat.keys():
            for l in boat['loads']:
                load_key = client.key("loads", l["id"])
                load = client.get(key=load_key)
                load["self"] = request.host_url + 'loads/' + str(load.key.id)
                load_list.append(load)
            return ({"loads": load_list}, 200)
        else:
            return ({"loads": []}, 200)
        