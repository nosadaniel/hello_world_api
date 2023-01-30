from datetime import timedelta
from fastapi import FastAPI, Path, Body, Header, Form, UploadFile, File, HTTPException, Depends,status
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import  OAuth2PasswordRequestForm
from jose import JWTError, jwt, ExpiredSignatureError

from app.models.model import ModelName, Item, BaseUser, UserIn, Token, TokenData, Image
from app.auth.auth import CustomAuth

app = FastAPI()

auth_instance:CustomAuth = CustomAuth(app= app)

oauth2_scheme = auth_instance.oauth2_scheme

pwd_context = auth_instance.pwd_context

SECRET_KEY = auth_instance.SECRET_KEY
ALGORITHM = auth_instance.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = auth_instance.ACCESS_TOKEN_EXPIRE_MINUTES



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


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials", 
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data: TokenData= TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="token has been expired")
    except JWTError:
        raise credentials_exception
    user = auth_instance.get_user(auth_instance.fake_user_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: BaseUser = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token, tags=["Token"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_instance.authenticate_user(fake_db=auth_instance.fake_user_db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers= {"WWW-Authenticate": "bearer"},
        )
    access_token_expires = timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_instance.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=BaseUser, tags=["user"])
def read_users_me(current_user: BaseUser = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items", tags=["user"])
def read_own_items(current_user: BaseUser = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.get("/auth/", tags=["OAuth"])
def auth(token: str = Depends(oauth2_scheme)):
    return {"token" : token}