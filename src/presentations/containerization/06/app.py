import os

import uvicorn
from fastapi import FastAPI

NAME = os.getenv("NAME", "Ben")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": f"Hello World from {NAME}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
