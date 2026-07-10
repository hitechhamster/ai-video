from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.routers import catalog, effect_presets, jobs, music, projects, styles, templates, voices
from app.seed import seed_builtin_effect_presets, seed_builtin_styles, seed_builtin_templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_builtin_styles()
    seed_builtin_effect_presets()
    seed_builtin_templates()
    yield


app = FastAPI(title="AI火柴人", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(styles.router)
app.include_router(effect_presets.router)
app.include_router(catalog.router)
app.include_router(projects.router)
app.include_router(jobs.router)
app.include_router(voices.router)
app.include_router(music.router)
app.include_router(templates.router)

app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")


@app.get("/health")
def health():
    return {"ok": True}
