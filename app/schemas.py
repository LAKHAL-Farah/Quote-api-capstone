from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional


class QuoteBase(BaseModel):
    text: str
    author: str
    category: Optional[str]= None


class QuoteCreate(QuoteBase):
    pass

class QuoteRead(QuoteBase):
    id:int
    created_at: datetime
    model_config= ConfigDict(from_attributes=True)