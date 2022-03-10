"""
FastAPI WebService OAuth from scratch
"""
import datetime
import random
import string
from typing import Optional
from fastapi import FastAPI, Form, Path, Depends, Header, Response, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

accounts = {
    1: {
        "name": "palito",
        "username": "palitojeremy",
        "email": "palito@ui.ac.id",
        "npm": "1706039793",
        "password": "123",
        "secret": "18045"
    }
}

cookies = {}
refresh = {}

CLIENT_ID = "123"
CLIENT_SECRET = "456"
EXPIRED = 300


class Account(BaseModel):
    name: str
    username: str
    email: str
    npm: str
    password: str


class Cookie(BaseModel):
    account_id: str
    refresh_token: str
    created_at: str


class UpdateAccount(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    npm: Optional[str] = None
    password: Optional[str] = None
    secret: Optional[str] = None


class UpdateCookie(BaseModel):
    account_id: Optional[str] = None
    refresh_token: Optional[str] = None
    created_at: Optional[str] = None


@app.get("/get-account/{account_id}")
def get_account(account_id: int = Path(None, description="the ID of the Student", gt=0)):
    return accounts[account_id]


@app.get("/get-by-name")
def get_student(*, name: Optional[str] = None):
    for account_id in accounts.items():
        if accounts[account_id]["name"] == name:
            return accounts[account_id]
    return {"Data": "Not Found"}


@app.post("/create-account/{account_id}")
def create_account(account_id: int, account: Account):
    if account_id in accounts:
        return {"Error": "Account already exists"}

    accounts[account_id] = account
    return accounts[account_id]


@app.post("/oauth/token")
def create_token(response: Response, account_id: int = Form(...), password: str = Form(...), grant_type: str = Form("password"),
                 client_id: str = Form(...), client_secret: str = Form(...)):
    if((client_id == CLIENT_ID) and (client_secret == CLIENT_SECRET)):
        if (account_id in accounts) and (accounts[account_id]["password"] == password):
            cookie = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(40))
            refresh_token = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(40))
            cookies[cookie] = {
                "account_id": account_id,
                "refresh_token": refresh_token,
                "created_at": datetime.datetime.now().timestamp()
            }
            refresh[refresh_token] = cookie
            return{
                "access_token": cookie,
                "expires_in": EXPIRED,
                "token_type": "Bearer",
                "scope": "null",
                "refresh_token": refresh_token
            }
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return{
            "error": "account_err",
            "error_description": "Account or password invalid"
        }
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return{
        "error": "client_err",
        "error_description": "client error"
    }


@app.post("/oauth/resource")
def authorize(response: Response, access_token: str = Header(...)):
    if(access_token.split(' ')[0] != "Bearer"):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return{
            "error": "no_authorization",
            "error_description": "Permission Denied"
        }
    token = access_token.split(' ')[1]
    now = datetime.datetime.now().timestamp()
    if (token in cookies) and (now - cookies[token]["created_at"] <= EXPIRED):
        account = accounts[cookies[token]["account_id"]]
        return {
            "access_token": token,
            "client_id": cookies[token]["account_id"],
            "user_id": account["username"],
            "full_name": account["name"],
            "npm": account["npm"],
            "expires": EXPIRED - (now - cookies[token]["created_at"]),
            "refresh_token": cookies[token]["refresh_token"]
        }
    response.status_code = status.HTTP_401_UNAUTHORIZED
    return{
        "error": "session_err",
        "error_description": "Session not found or expired"
    }


@app.get("/items/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}
