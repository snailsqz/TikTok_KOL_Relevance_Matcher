from fastapi import FastAPI
from sqlmodel import Session, select

from .database import engine, create_db_and_tables
from .models import Item
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .scraper import TiktokDataScraper
        
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL ของ Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    search_queries: list[str]
    api: str
    results_per_page: int
    brand_description: str
    desired_language: str
    weight_relevance: float
    weight_fans: float

@app.get("/")
def read_root():
    return {"message": "Welcome to the TikTok Scraper API"}

@app.post("/scrape/")
def scrape_data(request: ScrapeRequest):
    APIKEY = request.api
    scraper = TiktokDataScraper(APIKEY)
    scraper.get_data(request.search_queries, request.results_per_page)
    processed_brand_text = scraper.preprocess_data(
        request.brand_description, request.desired_language
    )
    final_results = scraper.find_similarity(
        processed_brand_text, request.weight_relevance, request.weight_fans
    )
    return {"message": "Analysis complete", "results": final_results}


# @app.get("/items/")
# def read_items():
#     with Session(engine) as session:
#         items = session.exec(select(Item)).all()
#         return items

# @app.post("/items/")
# def create_item(item: Item):
#     with Session(engine) as session:
#         session.add(item)
#         session.commit()
#         session.refresh(item)
#         return item

# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     with Session(engine) as session:
#         db_item = session.get(Item, item_id)
#         if not db_item:
#             return {"error": "Item not found"}
#         db_item.name = item.name
#         db_item.description = item.description
#         db_item.price = item.price
#         session.add(db_item)
#         session.commit()
#         session.refresh(db_item)
#         return db_item
    
# @app.delete("/items/{item_id}")
# def delete_item(item_id: int):
#     with Session(engine) as session:
#         db_item = session.get(Item, item_id)
#         if not db_item:
#             return {"error": "Item not found"}
#         session.delete(db_item)
#         session.commit()
#         return {"message": "Item deleted successfully"}
