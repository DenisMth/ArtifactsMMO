from pydantic import BaseModel

class Command(BaseModel):
    characters: list[str]
    action: str
    target: str | None = None
    option: str | None = None