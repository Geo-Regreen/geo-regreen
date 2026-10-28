from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve():
    return FileResponse("frontend/index.html")

# Real NDVI endpoint will go here - we wire next
@app.get("/api/ndvi/khwezela")
def get_ndvi():
    from src.indices.ndvi import get_khwezela_ndvi_timeseries
    return get_khwezela_ndvi_timeseries()