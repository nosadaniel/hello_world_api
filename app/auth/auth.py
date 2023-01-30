from datetime import datetime, timedelta

from fastapi import FastAPI
from jose import jwt
from passlib.context import CryptContext
from app.models.model import UserIn
from fastapi.security import OAuth2PasswordBearer


class CustomAuth:

    _app: FastAPI

    def __init__(self, app:FastAPI) -> None:
        self._app = app

    #get the token form the response header
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    #encryption
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

    SECRET_KEY = "bd6195727d6598ce7cbcc63698446ab21e1bb9791f654368b316656c638202aa"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 5


    fake_user_db = {
        "JohnDoe": {
            "username": "JohnDoe",
            "full_name": "John Doe",
            "email":"johndoe@email.com",
            "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "disabled" : False,
        }
    }

    def verify_password(self, plain_password, hashed_password) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password) -> str:
        return self.pwd_context.hash(password)
    
    def get_user(self, db: dict | None, username: str):
        if not db:
            user_dict = self.fake_user_db
        else:
            user_dict = db
        if username in db:
            user_dict = db[username]
        return UserIn(**user_dict)
    
    def authenticate_user(self, fake_db: dict, username: str, password: str):
        user = self.get_user(fake_db, username)
        if not user:
            return False
        if not self.verify_password(password, user.password):
            return False
        return user
    
    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt