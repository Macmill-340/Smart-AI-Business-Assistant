from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
import shutil
from pydantic import BaseModel
from backend.database import engine, Lead
import os
from agent.rag import process_document
from agent.agent import run_agent
from contextlib import asynccontextmanager
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from backend.database import create_db_and_table, get_session, User
from backend.auth import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
import jwt

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_table()
    yield
app = FastAPI(title="SAIBAP-Imperium-Prototype", lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#endpoints
@app.post("/register")
def register_user(username:str, password:str, role:str = "user", session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username==username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already registered")

    new_user = User(username=username, password_hash=get_password_hash(password), role=role)
    session.add(new_user)
    session.commit()
    return {"message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload.get("sub"), "role": payload.get("role")}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.post("/upload")
async def upload_doc(file: UploadFile = File(...)):
    """upload pdf for rag"""
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    #chunk and store
    result = process_document(file_path)

    #remove temp file
    os.remove(file_path)

    return {"message": result}

class ChatRequest(BaseModel):
    message: str
    history: str = ""

@app.post("/chat")
def chat(request: ChatRequest):
    """chat with the ai assistant"""
    response = run_agent(request.message, request.history)
    return {"reply": response}

@app.get("/leads")
def get_leads():
    """admin endpoint for leads"""
    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        return leads