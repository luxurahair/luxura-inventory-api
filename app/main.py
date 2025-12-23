import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.db.session import engine
from app.routes import wix as wix_routes

app = FastAPI(
    title="Luxura Inventory API",
    version="2.0.0",
)

# ----------------------------
#  CORS
# ----------------------------
origins_env = os.getenv("CORS_ORIGINS", "")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    # Dev seulement — en prod mets: ["https://www.luxuradistribution.com"]
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
#  ROUTES
# ----------------------------
app.include_router(wix_routes.router)

@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Luxura Inventory API",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# ----------------------------
#  STARTUP
# ----------------------------
@app.on_event("startup")
def on_startup() -> None:
    # Option: éviter de recréer les tables en prod si tu veux
    # if os.getenv("AUTO_CREATE_TABLES", "1") == "1":
    SQLModel.metadata.create_all(engine)
