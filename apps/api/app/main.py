from fastapi import FastAPI

from app.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="c3Ntr0l API",
        description="Backend for the AI personal operating system.",
        version="0.1.0",
    )

    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    def root_health_check():
        return {"status": "ok"}

    return app


app = create_app()
