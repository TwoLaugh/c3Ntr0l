from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
def get_current_user_placeholder():
    return {
        "authenticated": False,
        "user": None,
        "next": "Wire Google OAuth/OIDC token verification.",
    }
