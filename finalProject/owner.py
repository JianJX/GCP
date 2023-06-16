from flask import Blueprint, request
from google.cloud import datastore
import json
from auth import verify_jwt, ALGORITHMS, DOMAIN, CLIENT_ID, AuthError
from jose import jwt
from six.moves.urllib.request import urlopen

bp = Blueprint('owner', __name__, url_prefix='/owners')
client = datastore.Client()

@bp.route('', methods=['GET','POST'])
def owners_get_post():
    if 'application/json' not in request.accept_mimetypes:
        return ('Not Acceptable', 406)

    if request.method == 'POST':
        if request.is_json != True:
            return ('Unsupported Media Type', 415)
        payload = verify_jwt(request)
        if type(payload) == AuthError:
            return ('Unauthorized', 401)
        UID = payload["sub"]
        content = request.get_json()
        if "age" not in content or "fname" not in content or "lname" not in content:
            return ({"Error": "The request object is missing at least one of the required attributes"}, 400)
        new_owner = datastore.entity.Entity(key=client.key("owners"))
        new_owner.update({'age': content['age'], 'fname': content['fname'], 
        'lname': content['lname'], "cars": [], "UID": UID})
        client.put(new_owner)
        selfURL = request.base_url + '/' + str(new_owner.key.id)
        content["id"] = new_owner.key.id
        content["self"] = selfURL
        content["UID"] = UID
        content["cars"] = []
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
                            query = client.query(kind="owners")
                            results = list(query.fetch())
                            for e in results:
                                if e["UID"] == owner:
                                    e["self"] = request.base_url + '/' + str(e.key.id)
                                    return (e, 200)
                        except:
                            pass
            except:
                pass
        query = client.query(kind="owners")
        results = list(query.fetch())
        for e in results:
            del e['cars']
            e["self"] = request.base_url + '/' + str(e.key.id)
        return json.dumps(results)


@bp.route('/<id>', methods=['GET'])
def owners_get(id):
    owner_key = client.key("owners", int(id))
    owner = client.get(key=owner_key)
    if owner == None:
        return ({"Error": "No owner with this owner_id exists"}, 404)

    payload = verify_jwt(request)
    if type(payload) == AuthError:
        return ('Unauthorized', 401)
    UID = payload["sub"]

    if owner["UID"] != UID:
        return ('Forbidden', 403)

    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return ('Not Acceptable', 406)        
        response_body = {}
        response_body["id"] = int(id)
        response_body["age"] = owner["age"]
        response_body["fname"] = owner["fname"]
        response_body["lname"] = owner["lname"]
        response_body["cars"] = owner["cars"]
        response_body["self"] = request.base_url
        return (response_body, 200)
    ''' 
    if request.method == 'DELETE':
        client.delete(owner_key)
        return ('',204)

    if request.is_json != True:
        return ('Unsupported Media Type', 415)

    if request.method == 'PATCH':
        content = request.get_json()
        if "age" not in content and "fname" not in content and "lname" not in content:
            return ({"Error": "The request object provides none of the required attributes"}, 400)
        if "age" in content:
            owner.update({"age": content["age"]})
        if "fname" in content:
            owner.update({"fname": content["fname"]})
        if "lname" in content:
            owner.update({"lname": content["lname"]})
        client.put(owner)
        return ('',200)

    if request.method == 'PUT':
        content = request.get_json()
        if "age" not in content or "fname" not in content or "lname" not in content:
            return ({"Error": "The request object is missing at least one of the required attributes"}, 400)
        owner.update({"age": content["age"], "fname": content["fname"],
          "lname": content["lname"]})
        client.put(owner)
        return ('',200)
    '''
        