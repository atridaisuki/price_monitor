from typing import Optional,List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class ProductBase(SQLModel):
    name: str
    url:str
    platform: str =Field(default="steam")
    target_price: float

class Product(ProductBase,table=True):
    id: Optional[int] =Field(default=None,primary_key=True)
    current_price: Optional[float] =None
    last_checked_time: Optional[datetime] =None

    history:List["PriceHistory"]=Relationship(back_populates="product")

class PriceHistory(SQLModel,table=True):
    id: Optional[int] =Field(default=None,primary_key=True)
    price:float
    check_time:datetime =Field(default_factory=datetime.now)

    product_id:int =Field(foreign_key="product.id")
    product:Optional[Product] =Relationship(back_populates="history")
