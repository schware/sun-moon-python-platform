from __future__ import annotations

from fastapi import FastAPI


def create_http_app(service_name: str) -> FastAPI:
    app = FastAPI(title=service_name)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": service_name}

    return app
