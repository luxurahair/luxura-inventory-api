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

@app.head("/")
def root_head():
    return

@app.get("/health")
def health():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return
