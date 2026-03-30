from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.rag import router as rag_router
from utils.settings import CORS_ORIGINS

app = FastAPI(title="ETT API", version="1.0.0")

origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(rag_router, prefix="/api")