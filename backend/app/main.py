from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .config import APP_ENV, CORS_ORIGINS, FRONTEND_DIR, SECRET
from .routers import auth_routes, candidatures, dashboard, offres, profil

app = FastAPI(
    title="Entretien garanti",
    description="Espace de recherche d'emploi, de suivi des candidatures et de préparation aux entretiens.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_routes.router)
app.include_router(profil.router)
app.include_router(offres.router)
app.include_router(candidatures.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def startup():
    if APP_ENV == "production" and (
        SECRET.startswith("dev-") or len(SECRET) < 32 or "changez-moi" in SECRET.lower()
    ):
        raise RuntimeError("Configurez APP_SECRET avec au moins 32 caractères aléatoires en production.")
    db.init_db()


@app.get("/api/sante")
def sante():
    return {"ok": True, "service": "entretien-garanti"}


if FRONTEND_DIR.exists():
    static_dir = FRONTEND_DIR / "static"
    build_dir = FRONTEND_DIR / "dist"
    build_index = build_dir / "index.html"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    if (build_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=build_dir / "assets"), name="assets")

    @app.get("/")
    def index():
        if build_index.exists():
            return FileResponse(build_index)
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{spa_path:path}")
    def spa(spa_path: str):
        if spa_path.startswith("api/") or spa_path == "api":
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = (build_dir if build_index.exists() else FRONTEND_DIR) / spa_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(build_index if build_index.exists() else FRONTEND_DIR / "index.html")
