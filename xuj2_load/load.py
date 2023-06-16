from flask import Blueprint, request
from google.cloud import datastore
import json
#from json2html import *

client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        content = request.get_json()
        if "volume" not in content or "item" not in content or "creation_date" not in content:
            error_response = {}
            error_response["Error"] = "The request object is missing at least one of the required attributes"
            return (error_response, 400)
        new_load = datastore.entity.Entity(key=client.key("loads"))
        new_load.update({"volume": content["volume"], "item": content["item"], 
        "creation_date": content["creation_date"], "carrier": None})
        client.put(new_load)
        selfURL = request.base_url + '/' + str(new_load.key.id)
        #new_load.update({"self": selfURL})
        #client.put(new_load)
        content["id"] = new_load.key.id
        content["carrier"] = None
        content["self"] = selfURL
        return (content, 201)
    elif request.method == 'GET':
        query = client.query(kind="loads")
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e.key.id)
        output = {"loads": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)


@bp.route('/<id>', methods=['PUT','DELETE', 'GET'])
def loads_put_delete_get(id):
    if request.method == 'PUT':
        content = request.get_json()
        load_key = client.key("loads", int(id))
        load = client.get(key=load_key)
        guest.update({"carrier": content["carrier"]})
        client.put(load)
        return ('',200)
    elif request.method == 'DELETE':
        query = client.query(kind="loads")
        results = list(query.fetch())
        for e in results:
            if e.key.id == int(id):
                load_key = client.key("loads", int(id))
                load = client.get(key=load_key)
                bid = load["carrier"]["id"]
                boat_key = client.key("boats", bid)
                boat = client.get(key=boat_key)
                for l in boat["loads"]:
                    if l["id"] == int(id):
                        boat["loads"].remove(l)
                        client.put(boat)
                        break
                client.delete(load_key)
                return ('', 204)
        return ({"Error": "No load with this load_id exists"}, 404)
    elif request.method == 'GET':
        load_key = client.key("loads", int(id))
        load = client.get(key=load_key)
        if load == None:
            error_response = {}
            error_response["Error"] = "No load with this load_id exists"
            return (error_response, 404)
        load["id"] = load.key.id
        load["self"] = request.base_url
        if load["carrier"] != None:
            load["carrier"]["self"] = request.host_url + 'boats/' + str(load["carrier"]["id"])
        return json.dumps(load)
    else:
        return 'Method not recogonized'