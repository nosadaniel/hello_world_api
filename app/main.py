from fastapi import FastAPI, Path, Body, Header, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer

from app.models.model import ModelName, Item, BaseUser, UserIn, Image


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


fake_item_db = [{"item_name":"foo"},{"item_name":"Bar"},{"item_name":"Baz"}]

@app.get("/hello")
def read_root():
    return {"hello":"World"}

@app.get("/models/{model_name}")
def get_model(model_name: ModelName):
    return {"model_name": model_name, "message": "here you go"}

    
@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    return {"file_path": file_path}

@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return fake_item_db[skip: skip+limit]

@app.get("/items/{item_id}")
def read_item(item_id: str, q: str | None = None):
    if q is not None:
        return {"item_id": item_id, "q": q}
    return {"item_id":item_id}

@app.post("/items")
async def create_item(item: Item):
    item_dict: dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax":price_with_tax})
    return item_dict

@app.get("/special-item/{item_id}")
#order of args does not matter because of *
def read_special_item(*, item_id: int = Path("The ID of the item to get", ge=1), q:str) :
    results: dict = {"item_id":item_id}
    return results

@app.put("/special-item/{item_id}")
def update_special_item(item_id: int, item: Item, user: BaseUser, importance: int = Body(default=5) ):
    return {"item_id": item_id, "item":item, "user":user, "importance":importance}

@app.post("/images/multiple/")
def create_multiple_images(images: list[Image]) -> list[Image]:
    return images
@app.get("/get-headers")
def get_headers(user_agent:str | None = Header(default=None)):
    return {"user_agent" : user_agent}

@app.post("/user/", response_model=BaseUser)
def create_user(user: UserIn):
    return user
    
@app.post("/login/")
def login(username: str = Form(default=None), password: str = Form(default=None)):
    return {"username":username}

@app.post("/create-files/")
def create_files(files: list[bytes] = File(default=None, description="Multiple files as bytes")):
    return {"file_sizes": [len(file) for file in files]}

@app.post("/uploadfiles/")
def create_upload_files(files: list[UploadFile] = File(default=None, description="Multiple files as UploadFile")):
    return {"filenames": [file.filename for file in files]}



@app.get("/")
def main():
    content = """ 
        <body> 
            <form action="/create-files/" enctype="multipart/form-data" method="post">
                <input name="files" type="file" multiple>
                <input type="submit" value="create file">
            </form> 
            <form action="/uploadfiles/" enctype="multipart/form-data" method="post"> 
                <input name="files" type="file" multiple> 
                <input type="submit" value="upload file"> 
            </form> 
        </body>    
     """
    return HTMLResponse(content=content)

items = { "foo": {"name": "Foo", "price": 50.2}, "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2}, "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []}, }


@app.get("/new-items/{item_id}", response_model=Item, name="item", tags= ["new items"])
def get_new_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found", headers= {"X-Error": "There goes my error"})
    return items[item_id]

@app.patch("/new-items/{item_id}", response_model= Item, tags=["new items"])
def update_item(item_id: str, item: Item):
    stored_item_data = get_new_item(item_id)
    stored_item_model = Item(**stored_item_data)
    update_data = item.dict(exclude_unset=True)
    updated_item = stored_item_model.copy(update=update_data)
    items[item_id] = jsonable_encoder(updated_item)
    print(items[item_id])
    return updated_item

def common_para(q: str, skip: int = 0, limit: int = 0) -> dict:
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/common-items/", tags=["common items"])
def read_item(commons: dict = Depends(common_para)):
    return commons


async def verify_token(x_token: str = Header()): 
    if x_token != "fake-super-secret-token": 
        raise HTTPException(status_code=400, detail="X-Token header invalid") 
    
async def verify_key(x_key: str = Header()): 
    if x_key != "fake-super-secret-key": 
        raise HTTPException(status_code=400, detail="X-Key header invalid") 
    return x_key

@app.get("/depend-item/", dependencies=[Depends(verify_key), Depends(verify_token)])
def read_items():
    return [{"item": "foo", "item": "bar"}]

@app.get("/auth/", tags=["OAuth"])
def auth(token: str = Depends(oauth2_scheme)):
    return {"token" : token}