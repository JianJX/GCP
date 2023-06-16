from flask import Blueprint, Flask, request, jsonify, _request_ctx_stack, current_app
from functools import wraps
import requests
from six.moves.urllib.request import urlopen
from flask_cors import cross_origin
from jose import jwt
from os import environ as env
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
import json

bp = Blueprint('auth', __name__, url_prefix='/auth')

CLIENT_ID = 'yccd03hHHWy8DFV7S4Hlws2hWTRwRKE5'
CLIENT_SECRET = 'zZxi0DGJvV9J-l50zIj5jSTYqVcaKHASjUuNil_zuPcrodEdRLmct0K_ojpaMagq'
DOMAIN = 'project7.us.auth0.com'
ALGORITHMS = ["RS256"]
oauth = OAuth(current_app)
auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)

def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        return AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        return AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        return AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
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
        except jwt.ExpiredSignatureError:
            return AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            return AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            return AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        return AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@bp.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

@bp.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        content = request.get_json()
        email = content["username"]
        password = content["password"]
        url = "https://" + DOMAIN + "/oauth/token"
        audience = "https://" + DOMAIN + "/api/v2/"
        headers = {'content-type': "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "audience": audience
        }
        res = requests.post(url, headers=headers, data=data)
        token = res.json()["access_token"]
        url = "https://" + DOMAIN + "/api/v2/users"
        headers = {'Authorization': "Bearer {}".format(token)}
        body = {
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication"
        }
        res = requests.post(url, headers=headers, json=body)
        body = {'grant_type':'password',
                'username':email,
                'password':password,
                'client_id':CLIENT_ID,
                'client_secret':CLIENT_SECRET
        }
        headers = { 'content-type': 'application/json' }
        url = 'https://' + DOMAIN + '/oauth/token'
        res = requests.post(url, json=body, headers=headers)
        return (res.json(), 200)

@bp.route('/login', methods=['POST'])
def login_user():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    body = {'grant_type':'password','username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    return r.text, 200, {'Content-Type':'application/json'}
