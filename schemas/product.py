from pydantic import BaseModel,ConfigDict


class ProductCreate(BaseModel):
    name: str
    price: int
    stock: int

class ProductUpdate(BaseModel):
    name: str
    price: int
    stock: int

class ProductReturn(BaseModel):
    id:int
    name: str
    price: int
    stock: int
    
    model_config=ConfigDict(from_attributes=True)

class ProductPageReturn(BaseModel):
    page:int
    limit:int
    total:int
    total_pages:int
    items:list[ProductReturn]
    
    model_config=ConfigDict(from_attributes=True)