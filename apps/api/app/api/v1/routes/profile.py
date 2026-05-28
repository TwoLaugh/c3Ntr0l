from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_profile_placeholder():
    return {
        "profile": None,
        "next": "Return the authenticated user's declared and learned profile.",
    }
