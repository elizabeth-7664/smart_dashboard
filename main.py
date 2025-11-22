from fastapi import FastAPI
from app.routers import sales
from app.services.sales_analysis import router as analysis_router

app = FastAPI(title="Smart Dashboard API")


app.include_router(sales.router, prefix="/api", tags=["Sales"])
app.include_router(analysis_router)

@app.get("/")
def root():
    return {"message": "Smart Dashboard API is running"}
