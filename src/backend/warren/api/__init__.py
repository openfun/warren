"""Warren API root."""
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    """Temporary root URL."""
    return {"Hello": "World"}
