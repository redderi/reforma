from dataclasses import dataclass, field
from uuid import UUID
from typing import List, Dict

@dataclass
class Survey:
    id: UUID
    owner_id: UUID
    title: str
    description: str | None = None
    questions: List[UUID] = field(default_factory=list) # ID вопросов
    settings: Dict = field(default_factory=dict)      
    template_id: UUID | None = None                     
    published: bool = False