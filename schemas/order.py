from pydantic import BaseModel,ConfigDict,Field

class OrderCreate(BaseModel):
    product_id: int
    amount: int=Field(gt=0)
    
class OrderUserReturn(BaseModel):
    id:int
    name:str
    model_config=ConfigDict(from_attributes=True)
    
class OrderProductReturn(BaseModel):
    id:int
    name:str
    price:int
    model_config=ConfigDict(from_attributes=True)

class OrderReturn(BaseModel):
    
    id:int
    amount:int
    user:OrderUserReturn
    product:OrderProductReturn
    model_config=ConfigDict(from_attributes=True)
    
class OrderUpdate(BaseModel):
    amount:int=Field(gt=0)    

