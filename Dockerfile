FROM python:3.10

#create working directory in the image
WORKDIR /hello_world_api

#copy requirement file to the newly created dir
COPY ./requirements.txt /hello_world_api/requirements.txt

#install package dependencies
# --no-cache-dir tells pip not to save locally
RUN pip install --no-cache-dir --upgrade -r /hello_world_api/requirements.txt

#copy app directory to hello_world_api directory
COPY ./app /hello_world_api/app

CMD ["uvicorn", "app.main:app", "--proxy-headers" ,"--host", "0.0.0.0","--port", "80"]