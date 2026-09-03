from fastapi import FastAPI

from app.database import init_db
from app.routes import documents, fact

app = FastAPI()

app.include_router(documents.router)
app.include_router(fact.router)


@app.get("/")
async def main():
    return {"message": "hello"}


init_db()
