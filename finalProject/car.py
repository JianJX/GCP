from flask import Blueprint, request
from google.cloud import datastore
import json
from auth import verify_jwt, ALGORITHMS, DOMAIN, CLIENT_ID, AuthError
from jose import jwt
from six.moves.urllib.request import urlopen

bp = Blueprint('car', __name__, url_prefix='/cars')
client = datastore.Client()

@bp.route('', methods=['GET','POST'])
def cars_get_post():
    if 'application/json' not in request.accept_mimetypes:
        return ('Not Acceptable', 406)

    if request.method == 'POST':
        if request.is_json != True:
            return ('Unsupported Media Type', 415)
        content = request.get_json()
        if "brand" not in content or "color" not in content or "license" not in content:
            return ({"Error": "The request object is missing at least one of the required attributes"}, 400)
        payload = verify_jwt(request)
        if type(payload) == AuthError:
            return ('Unauthorized', 401)
        UID = payload["sub"]
        new_car = datastore.entity.Entity(key=client.key("cars"))
        new_car.update({'brand': content['brand'], 'color': content['color'], 
        'license': content['license'], 'owner': UID, "parking": None})
        client.put(new_car)
        selfURL = request.base_url + '/' + str(new_car.key.id)
        content["id"] = new_car.key.id
        content["self"] = selfURL
        content["owner"] = UID
        query = client.query(kind="owners")
        results = list(query.fetch())
        for e in results:
            if e["UID"] == UID:
                e["cars"].append(new_car.key.id)
                client.put(e)
        return (content, 201)

    if request.method == 'GET':
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization'].split()
            token = auth_header[1]
            jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
            jwks = json.loads(jsonurl.read())
            try:
                unverified_header = jwt.get_unverified_header(token)
                if unverified_header["alg"] == "RS256":
                    rsa_key = {}
                    for key in jwks["keys"]:
                        if key["kid"] == unverified_header["kid"]:
                            rsa_key = {
                                "kty": key["kty"],
                                "kid": key["kid"],
                                "use": key["use"],
                                "n": key["n"],
                                "e": key["e"]
                            }
                    if rsa_key:
                        try:
                            payload = jwt.decode(
                                token,
                                rsa_key,
                                algorithms=ALGORITHMS,
                                audience=CLIENT_ID,
                                issuer="https://"+ DOMAIN+"/"
                            )
                            owner = payload["sub"]
                            query = client.query(kind="cars")
                            results = list(query.fetch())
                            car_list = []
                            for e in results:
                                if e["owner"] == owner:
                                    e["self"] = request.base_url + '/' + str(e.key.id)
                                    car_list.append(e)
                            return ({"cars": car_list}, 200)
                        except:
                            pass
            except:
                pass
        query = client.query(kind="cars")
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
            e["self"] = request.base_url + '/' + str(e.key.id)
        output = {"total_cars": total, "cars": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output)

@bp.route('/<id>', methods=['GET','DELETE','PATCH','PUT'])
def cars_get_delete_patch_put(id):
    car_key = client.key("cars", int(id))
    car = client.get(key=car_key)
    if car == None:
        return ({"Error": "No car with this car_id exists"}, 404)

    payload = verify_jwt(request)
    if type(payload) == AuthError:
        return ('Unauthorized', 401)
    UID = payload["sub"]

    if car["owner"] != UID:
        return ('Forbidden', 403)

    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return ('Not Acceptable', 406)        
        response_body = {}
        response_body["id"] = int(id)
        response_body["brand"] = car["brand"]
        response_body["color"] = car["color"]
        response_body["license"] = car["license"]
        response_body["owner"] = car["owner"]
        response_body["parking"] = car["parking"]
        response_body["self"] = request.base_url
        return (response_body, 200)

    if request.method == 'DELETE':
        query = client.query(kind="owners")
        results = list(query.fetch())
        for e in results:
            for c in e["cars"]:
                if c == car.key.id:
                    e["cars"].remove(c)
                    client.put(e)
                    client.delete(car_key)
                    return ('',204)

    if request.is_json != True:
        return ('Unsupported Media Type', 415)

    if request.method == 'PATCH':
        content = request.get_json()
        if "brand" not in content and "color" not in content and "license" not in content:
            return ({"Error": "The request object provides none of the required attributes"}, 400)
        if "brand" in content:
            car.update({"brand": content["brand"]})
        if "color" in content:
            car.update({"color": content["color"]})
        if "license" in content:
            car.update({"license": content["license"]})
        client.put(car)
        return ('',200)

    if request.method == 'PUT':
        content = request.get_json()
        if "brand" not in content or "color" not in content or "license" not in content:
            return ({"Error": "The request object is missing at least one of the required attributes"}, 400)
        car.update({"brand": content["brand"], "color": content["color"],
          "license": content["license"]})
        client.put(car)
        return ('',200)

        