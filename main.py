import os

from dotenv import load_dotenv
from fastapi import FastAPI


load_dotenv()  # take environment variables from .env.
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


