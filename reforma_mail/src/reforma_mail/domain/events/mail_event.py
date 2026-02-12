from dataclasses import dataclass
from typing import Literal, Dict, Any

EventType = Literal[
    "EMAIL_VERIFICATION",
    "PASSWORD_RESET",
    "SURVEY_REPORT"
]

@dataclass
class MailEvent:
    type: EventType
    payload: Dict[str, Any]
