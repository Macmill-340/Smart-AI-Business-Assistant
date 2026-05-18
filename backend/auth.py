import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta, timezone
import bcrypt


load_dotenv()

SECRET_KEY = os.getenv('SECRET_ENV_KEY')
ALGORITHM = os.getenv('ALGORITHM_ENV_KEY')

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data:dict, expires_delta: timedelta=timedelta(hours=2)):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt