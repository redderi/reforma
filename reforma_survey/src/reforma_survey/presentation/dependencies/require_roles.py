from fastapi import Depends, HTTPException
from reforma_survey.presentation.dependencies import get_current_user_role


def require_roles(*allowed_roles: str):
    def checker(role: str = Depends(get_current_user_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")

    return checker
