from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    value: float

@app.get("/api/data")
async def read_data():
    return {"message": "Hello from FastAPI!"}

@app.post("/api/data")
async def create_item(item: Item):
    return {"received": item}
