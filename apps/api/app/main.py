import importers.santander_br  # noqa: F401 — registers importers on startup

from fastapi import FastAPI

app = FastAPI(title="Finance OS", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
