from sqlmodel import Field, SQLModel, Session, create_engine
from typing import Optional

# user table
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="user")

# lead table
class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None
    intent: str = Field(default="cold")
    notes: Optional[str] = None

#Connect
sqlite_url = "sqlite:///./assistant.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_table():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session