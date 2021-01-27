from pydantic import BaseModel
from typing import Optional


class Technology(BaseModel):
    id: int
    name: str
    is_main_tech: Optional[bool]
