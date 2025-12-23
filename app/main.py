# ----------------------------
#  ROUTES
# ----------------------------
app.include_router(wix_routes.router)
# ----------------------------
#  ROUTES
# ----------------------------
app.include_router(wix_routes.router)

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "ok": True,
        "service": "Luxura Inventory API",
        "docs": "/docs",
        "health": "/health",
    }

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
