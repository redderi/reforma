from dataclasses import dataclass


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    template: str
    context: dict
