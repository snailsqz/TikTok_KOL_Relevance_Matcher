from fastapi import FastAPI
from sqlmodel import Session, select

from .database import engine, create_db_and_tables
from .models import Item
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
        
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL ของ Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EchoRequest(BaseModel):
    text: str
    
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return message

@app.post("/")
def echo_text(request: EchoRequest):
    global message
    
    message = {"message": request.text}
    return message


@app.get("/items/")
def read_items():
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items

@app.post("/items/")
def create_item(item: Item):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    with Session(engine) as session:
        db_item = session.get(Item, item_id)
        if not db_item:
            return {"error": "Item not found"}
        db_item.name = item.name
        db_item.description = item.description
        db_item.price = item.price
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item
    
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    with Session(engine) as session:
        db_item = session.get(Item, item_id)
        if not db_item:
            return {"error": "Item not found"}
        session.delete(db_item)
        session.commit()
        return {"message": "Item deleted successfully"}
