from fastapi import FastAPI

app = FastAPI(title="JARVIS INFINITY")

@app.get("/")
def home():
    return {"system": "JARVIS INFINITY", "status": "online"}
