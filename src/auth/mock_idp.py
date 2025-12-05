"""
Mock Identity Provider implementation with JWT formatting

Installs:
pip install uvicorn fastapi jwt pydantic rsa

Run (from root directory):
uv run python -m uvicorn src.mock_idp:app --host 127.0.0.1 --port 9400
"""

import base64
import jwt
import time
import uuid
from fastapi import FastAPI, Form, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

# Local imports
from src.models.auth import RegistrationRequest

ISSUER_URL = "http://127.0.0.1:9400"

EXP_TIME = 600 #(seconds)

auth_codes = {}
users = {
    "test-client": {
        "sub": "test-client",
        "roles": [],
        "organizations": []
    },
    "james_smith": {
        "sub": "james_smith",
        "roles": [],
        "organizations": ["Dallas_Police"]
    },
    "linda_baker": {
        "sub": "linda_baker",
        "roles": [],
        "organizations": ["Dallas_Police"]
    },
    "terry_jobs": {
        "sub": "terry_jobs",
        "roles": [],
        "organizations": ["Dallas_Police"]
    },
    "paul_morgan": {
        "sub": "paul_morgan",
        "roles": [],
        "organizations": ["Allen_Firestation"]
    },
    "admin": {
        "sub": "admin",
        "roles": ["admin"],
        "organizations": []
    }
}

# Pregenerated keys (+ mod and exp) for better runtime
pem_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEqQIBAAKCAQEAji1aAu+XgCQG4cwnrnq71Toul9wU/mZjD0ukz6JUFQTL4Yms
HHEuSNpz5iCjKp/XH0HBuQHXCE9oenJK6YUNabS+56JCXTIlLdUNomsKcsSdQN8F
8p+x+s39fAcbsZl8lKSTiMXBtMp95KfxLE6JJ+KPbmcZ+GVKzPXtEt5rYYwZ2LON
B5L13KtWpR+9RZtsF7o5PvkmovNO29sAs7IvunRep+idtE8k6vnM57Z2jVhCsO4L
R5dN4OMinVLqYav37JXIgFYsocJqyEOHcjxY+q8ZxsXnNSmp3Mv/EQsgPitOvL0H
tDp4ku2Euqt7Vl9AeMJD+MILKjtA0vKm4RTgXwIDAQABAoIBABSWeJxIOXXywZRc
zbo0R5K+1BRlaBzWkq2aVIlEhkxs32EPYH7V3M/r4jCGtVnsv2flS7oQjCTF6ukg
N7zM6X5PD/3Wvyljo4KZgVntihvIYMUOBnx1p34b6gLVvKrhAOs9UafSixQ05joA
H6o8zRubcQ2ZnGcds7sHGK+JtrsybpEIagCCVB5Ijxs6dBVf+syFmYAvzFGmqnnA
1uF8/wnUcndyjH8GZAYoYGK8jHyUgHm2lp3oeMKO4OIPvA0sj35cqJkKTj0MiA1I
pi3Z5fQbMOgFSlZvFsdEwVmqZgvUqjAqqJ3r1ylekvuyqxHNin3awIPQxf9n9rJU
KVWvdYECgYkAmPunFNqwhbelbvvfOhBTqd7VVHCIkIe19oTtiSGUq3C10N5wZ2mf
kh0lLBETWZehdROj7ly61VWse2bM/2qmw0sJD0j1pqetT9+UzRNhodN1NLRh/vyF
/MeXsUB2mKh37ztOJDhdO/xGnvqIYNWHwDrH5GNpGc0M+07tjzMNOGd3tuSiMtmF
oQJ5AO3q52/U1xCT22JYO5tYvTdHL+hsMhD6lOey4KZkYkzSs1bL0tudlVi4B+ka
OpptFwWVIedDGPvbZKboZFwB/mbq8/OeV5HxlQuuq1beu92wb0b6BJ9oXSB22zb1
I+eVBNOH2WuM9q/5dFpm5/x28/yEJtJpMkil/wKBiDUiIlPB6NFoiVLUtCFMjmJP
fLSJKUVZfT+Tx5R7T1GEIgHbYBrquntbGBAIFjplybQKEEO3fUSfLvrlJ4oGlsj5
hLoEUx2A21cEhn/7nUtBUFHv3KFdP4QeJndvtkErMgyrAmbeFLPC2RxaU4eeYjnH
sKmIRXaqmzmlnijASHUwqomhOxyCJEECeQC0PV5h0VuwmmL8SR23HW4TX6HCsZzo
Uf3W3iPkym3SB1mH6tfuOp623IxZot48uWJUf1t06NcXjmjdLXdCYNxLObngmNd8
oAkrFYOGRy0J0K0slyJDZXwPqRt/sg0mVzWVzvf+y4bjX9cu2YDsOW2zoqYKh1lp
wh8CgYglsbH7mXTM+HPkjmxVfD2jM6UFDbVDDs7cjaJl0vkRMoEzW7gZEu+GQULG
hzwS4Nod5TsJykIzDngmO5v9ufTChMpsD9QSVa+0gF5dQtbuJkVK4SHlj4XKZ48g
ZXRhBoqCxLLc95pxjFm+UdQNzpVpC8O5el41VeSvYKBLBngZCmuTKZyJKqB5
-----END RSA PRIVATE KEY-----"""

# base64 url encode modulus and exponent
n = """ji1aAu-XgCQG4cwnrnq71Toul9wU_mZjD0ukz6JUFQTL4YmsHHEuSNpz5iCjKp_XH0HBuQHXCE9oenJK6YUNabS
-56JCXTIlLdUNomsKcsSdQN8F8p-x-s39fAcbsZl8lKSTiMXBtMp95KfxLE6JJ-KPbmcZ
-GVKzPXtEt5rYYwZ2LONB5L13KtWpR-9RZtsF7o5PvkmovNO29sAs7IvunRep
-idtE8k6vnM57Z2jVhCsO4LR5dN4OMinVLqYav37JXIgFYsocJqyEOHcjxY
-q8ZxsXnNSmp3Mv_EQsgPitOvL0HtDp4ku2Euqt7Vl9AeMJD-MILKjtA0vKm4RTgXw"""

# Create JWK
jwk = {
    "kty": "RSA",
    "n": n,
    "e": "AQAB"
}

# Create API
app = FastAPI()

# ENDPOINTS
@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    return {
        "authorization_endpoint": f"{ISSUER_URL}/auth",
        "issuer": ISSUER_URL,
        "jwks_uri": f"{ISSUER_URL}/jwks",
        "token_endpoint": f"{ISSUER_URL}/token",
        "registration_endpoint": f"{ISSUER_URL}/register",
    }

@app.get("/auth")
async def auth(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    state: str = Query(...)
):
    # Query login endpoint, passing auth arguments
    arguments = f"client_id={client_id}&redirect_uri={redirect_uri}&state={state}"

    login_url = f"{ISSUER_URL}/login?{arguments}"
    return RedirectResponse(login_url, status_code = 302)

@app.get("/jwks")
async def jwks():
    return {"keys": [jwk]}

@app.get("/login", response_class = HTMLResponse)
async def login_get(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    state: str = Query(...)
):
    # Display HTML login form, expecting user_id input
    form = f"""
    <html>
    <head>
        <title>Mock IDP</title>
        <style>
            form {{
                margin: 50px auto;
                width: 400px;
                padding: 20px;
                box-shadow: 0 0 10px #111111;
                background-color: #babcff;
                border: 1px solid #111111;
                border-radius: 5px;  
            }}
        body {{
            font-family: 'Sans', serif;
            text-align: center;
        }}
        h1 {{
            font-size: 18px;
        }}
        p {{
            font-size: 12px;
        }}
        </style>
    </head>
    <body>
        <form method="post" action="{ISSUER_URL}/login">
            <h1><label for="user_id">User ID:  </label>
            <input type="text" id="user_id" name="user_id" required><br><h1>
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="state" value="{state}">
            <input type="submit" value="submit"><br>
            <p>(try admin or test-client)<p>
        </form>
    </body>
    <html>
    """
    return form
    
@app.post("/login")
async def login_post(
    user_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(...)
):
    # Check user id, redirect to error url if not found
    if user_id not in users:
        error_url = f"{redirect_uri}?error=access_denied&state={state}"
        return RedirectResponse(error_url, status_code = 302)

    # Add new auth code to auth code database
    auth_code = str(uuid.uuid4())
    exp = int(time.time()) + EXP_TIME

    auth_codes[auth_code] = {
        "user_id": user_id,
        "exp": exp,
    }

    # Redirect to successful login url
    redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
    return RedirectResponse(redirect_url, status_code = 302)

@app.post("/register")
async def register(request: RegistrationRequest):
    new_client_id = str(uuid.uuid4())

    # Check for redirect uri(s)
    if not request.redirect_uris:
        raise HTTPException(status_code = 400, detail = "redirect_uris required")

    return {
        "client_id": new_client_id,
        "redirect_uris": request.redirect_uris
    }

@app.post("/token")
async def token(
    code: str = Form(...)
):
    # Retrieve auth code
    if code not in auth_codes:
        raise HTTPException(status_code = 400, detail = "invalid auth code")
    
    auth_info = auth_codes[code]

    if auth_info["exp"] < time.time():
        raise HTTPException(status_code = 400, detail = "auth code expired")
    
    # Generate tokens
    user_info = users.get(auth_info["user_id"])
    if user_info is None:
        raise HTTPException(status_code = 401, detail = "user id not found")

    # Multi-audience token: valid for ALL MCP servers (SSO)
    access_claims = {
        "iss": ISSUER_URL,
        "aud": [
            "http://127.0.0.1:9000",  # Ticketing server
            "http://127.0.0.1:9001",  # Organizations server
            # Add new MCP server audiences here
        ],
        "sub": user_info["sub"],
        "roles": user_info["roles"],
        "organizations": user_info["organizations"],
        "exp": int(time.time()) + EXP_TIME,  # Token expiration
        "iat": int(time.time())  # Issued at
    }

    access_token = jwt.encode(
        payload = access_claims,
        key = pem_private_key,
        algorithm = 'RS256'
    )

    return {"access_token": access_token}