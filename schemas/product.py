from pydantic import BaseModel,ConfigDict,Field


class ProductCreate(BaseModel):
    name: str
    price: int
    stock: int
    description: str | None = None

class ProductUpdate(BaseModel):
    name: str
    price: int
    stock: int
    description: str | None = None

class ProductReturn(BaseModel):
    id:int
    name: str
    price: int
    stock: int
    description: str | None = None
    
    model_config=ConfigDict(from_attributes=True)

class ProductPageReturn(BaseModel):
    page:int
    limit:int
    total:int
    total_pages:int
    items:list[ProductReturn]
    
    model_config=ConfigDict(from_attributes=True)

class ProductStockUpdate(BaseModel):
    amount:int=Field(gt=0)