from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel,Field
from typing import Optional, List, Dict,Union


app = FastAPI(title="FastAPI")
class Data(BaseModel):
    total : Optional[int]  = Field(
        ...,gt=0,
        description= "Total amount"
    )
    month : Optional[Union[int,str,float]] = Field(
        ... , lt=10,gt=1,
        description= "months between 1 to 10"
    )
        
    
@app.get("/home")
def func():
    return {
        "Message" : "Welcome to the gen-ai world",
        "Status" : "Success"
    }

@app.post("/profit_company")
async def process_data(data:Data):
    return {"message" : data.total * data.month}
    
# @app.get("/total_profit")
# async def total_benefit():
#     import requests
#     response = requests.post(
#         url = "http://localhost:8000/profit_company",
#         json = {
#             "total" : 5000,
#             "month" : 5
#         },
#         headers={"Content-Type": "application/json"}
#     )
#     if response.raise_for_status == 200:
#         return response.json()

@app.get("/total_profit")
async def total_benefit():
    data = Data(total=5000, month=5)
    return await process_data(data)


if __name__ == "__main__":
    uvicorn.run(app,host="0.0.0.0",port="8000")