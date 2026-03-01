from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

#模式

class ProductBaseSchema(SQLModel):
    name:str
    url:str
    platform:str="steam"
    target_price:float

class ProductCreate(ProductBaseSchema):
    pass

class ProductRead(ProductBaseSchema):
    id:int
    current_price:Optional[float]=None
    last_checked_time:Optional[datetime]=None

class ProductUpdate(SQLModel):
    name:Optional[str]=None
    url:Optional[str]=None
    platform:Optional[str]=None
    target_price:Optional[float]=None
    current_price:Optional[float]=None
    last_checked_time:Optional[datetime]=None

class PriceHistoryRead(SQLModel):
    id:int
    price:float
    check_time:datetime
    product_id:int