from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.inference import router as inference_router
from routes.ingestion import router as ingestion_router
from routes.eval import router as eval_router
from routes.auth import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8501", "http://localhost:3000", "http://127.0.0.1:3000", "null", "https://striderr1o1.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inference_router)
app.include_router(ingestion_router)
app.include_router(eval_router)
app.include_router(auth_router)

