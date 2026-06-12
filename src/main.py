from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.inference import router as inference_router
from routes.ingestion import router as ingestion_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8501/", "http://localhost:3000", "http://127.0.0.1:3000", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inference_router)
app.include_router(ingestion_router)

