from fastapi import FastAPI, Query, Path, Depends, HTTPException, Body, APIRouter
from fastapi.responses import StreamingResponse
from app.schemas import auth
from app.db import database
from app.helpers import auth
from sqlalchemy.orm import Session


app = FastAPI()
router = APIRouter(prefix="/auth", tags=["Auth"])

@app.on_event("startup")
def startup():
    database.Base.metadata.create_all(bind=database.engine)

@router.post("/register")
def register(username: str = Body(...), password: str = Body(...), db: Session = Depends(auth.get_db)):
    existing = db.query(auth.User).filter(auth.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = auth.User(username=username, hashed_password=auth.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User registered"}

@router.post("/login")
def login(username: str = Body(...), password: str = Body(...), db: Session = Depends(auth.get_db)):
    user = db.query(auth.User).filter(auth.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}