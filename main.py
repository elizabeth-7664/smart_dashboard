from fastapi import FastAPI
from app.routers import sales

app = FastAPI(title="Smart Dashboard API")


app.include_router(sales.router, prefix="/api", tags=["Sales"])

@app.get("/")
def root():
    return {"message": "Smart Dashboard API is running"}
