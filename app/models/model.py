from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, EmailStr

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

class Image(BaseModel):
    url: HttpUrl
    name: str

    class Config:
        schema_extra = {
            "example" : {
                "url": "https://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers",
                "name" : "Foo"
            }
        }


class Item(BaseModel):
    name: str
    description: str | None = Field(default=None, title="The description of the item", max_length=300)
    price: float = Field(gt=0, description="the price must be greater than zero")
    tax: float | None = None
    images: set[Image] = set()
    tags: list[str] = []

    class Config:
        schema_extra = {
            "example" : {
                "name" : "Foo",
                "description": "A very nice Item",
                "price" : 35.4,
                "tax" : 2
            }
        }


class BaseUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserIn(BaseUser):
    password: str

class Offer(BaseModel):
    items: list[Item]

