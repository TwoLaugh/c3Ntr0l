from fastapi import APIRouter

from app.api.v1.routes import ai_actions, auth, domains, health, profile, projects, tasks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(ai_actions.router, prefix="/ai-actions", tags=["ai-actions"])
api_router.include_router(health.router, tags=["health"])
