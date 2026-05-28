from fastapi import APIRouter

from app.api.v1.routes import (
    ai_actions,
    auth,
    context_sections,
    domains,
    entries,
    health,
    inbox,
    profile,
    projects,
    reviews,
    routines,
    tasks,
    today,
    weekly_planning,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(context_sections.router, prefix="/context-sections", tags=["context-sections"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(routines.router, prefix="/routines", tags=["routines"])
api_router.include_router(today.router, prefix="/today", tags=["today"])
api_router.include_router(weekly_planning.router, prefix="/weekly-planning", tags=["weekly-planning"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(ai_actions.router, prefix="/ai-actions", tags=["ai-actions"])
api_router.include_router(health.router, tags=["health"])
