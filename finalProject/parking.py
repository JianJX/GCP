from flask import Blueprint, request
from google.cloud import datastore
import json
from auth import verify_jwt, ALGORITHMS, DOMAIN, CLIENT_ID, AuthError
from jose import jwt
from six.moves.urllib.request import urlopen

bp = Blueprint('parking', __name__, url_prefix='/parkings')
client = datastore.Client()

@bp.route('', methods=['GET','POST'])
def parkings_get_post():
    if 'application/json' not in request.accept_mimetypes:
        return ('Not Acceptable', 406)

    if request.method == 'POST':
        if request.is_json != True:
            return ('Unsupported Media Type', 415)
        content = request.get_json()
        if "number" not in content or "type" not in content or "private" not in content:
            return ({"Error": "The request object is missing at least one of the required attributes"}, 400)
        new_parking = datastore.entity.Entity(key=client.key("parkings"))
        new_parking.update({'number': content['number'], 'type': content['type'], 
        'private': content['private'], 'current_car': None})
        client.put(new_parking)
        selfURL = request.base_url + '/' + str(new_parking.key.id)
        content["id"] = new_parking.key.id
        content["self"] = selfURL
        return (content, 201)

    if request.method == 'GET':
        query = client.query(kind="parkings")
        total = len(list(query.fetch()))
        q_limit = int(request.args.get('limit', '5'))
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
        output = {"total_parkings": total, "parkings": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)

@bp.route('/<id>', methods=['GET','DELETE','PATCH','PUT'])
def parkings_get_delete_patch_put(id):
    parking_key = client.key("parkings", int(id))
    parking = client.get(key=parking_key)
    if parking == None:
        return ({"Error": "No parking with this parking_id exists"}, 404)

    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return ('Not Acceptable', 406)        
        response_body = {}
        response_body["id"] = int(id)
        response_body["number"] = parking["number"]
        response_body["type"] = parking["type"]
        response_body["private"] = parking["private"]
        response_body["current_car"] = parking["current_car"]
        response_body["self"] = request.base_url
        return (response_body, 200)

    if request.method == 'DELETE':
        query = client.query(kind="cars")
        results = list(query.fetch())
        for e in results:
            if e["parking"] == parking.key.id:
                e["parking"] = None
                client.put(e)
                break
        client.delete(parking_key)
        return ('',204)

    if request.is_json != True:
        return ('Unsupported Media Type', 415)

    if request.method == 'PATCH':
        content = request.get_json()
        if "number" not in content and "type" not in content and "private" not in content:
            return ({"Error": "The request object provides none of the required attributes"}, 400)
        if "number" in content:
            parking.update({"number": content["number"]})
        if "color" in content:
            parking.update({"type": content["type"]})
        if "private" in content:
            parking.update({"private": content["private"]})
        client.put(parking)
        return ('',200)

    if request.method == 'PUT':
        content = request.get_json()
        if "number" not in content or "type" not in content or "private" not in content:
            return ({"Error": "The request object is missing at least one of the required attributes"}, 400)
        parking.update({"number": content["number"], "type": content["type"],
          "private": content["private"]})
        client.put(parking)
        return ('',200)

@bp.route('/<pid>/cars/<cid>', methods=['DELETE','PUT', 'PATCH'])
def car_park_unpark(cid,pid):
    parking_key = client.key("parkings", int(pid))
    parking = client.get(key=parking_key)
    car_key = client.key("cars", int(cid))
    car = client.get(key=car_key)
    if request.method == 'PUT' or request.method == 'PATCH':
        if parking == None or car == None:
            return ({"Error": "The specified car and/or parking does not exist"}, 404)
        if parking["current_car"] != None:
            return ({"Error": "The specified parking is already occupied by another car"}, 400)
        parking.update({"current_car": int(cid)})
        client.put(parking)
        car.update({"parking": int(pid)})
        client.put(car)
        query = client.query(kind="parkings")
        results = list(query.fetch())
        for e in results:
            if e.key.id != int(pid) and e["current_car"] == int(cid):
                e["current_car"] = None
                client.put(e)        
        return ("", 204)
    elif request.method == 'DELETE':
        if parking == None or car == None:
            return ({"Error": "The specified car and/or parking does not exist"}, 404)
        if parking["current_car"] != int(cid):
            return ({"Error": "The specified car is not in this specified parking"}, 400)
        parking.update({"current_car": None})
        client.put(parking)
        car.update({"parking": None})
        client.put(car)
        return ("", 204)