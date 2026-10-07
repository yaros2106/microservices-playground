from fastapi import FastAPI

app = FastAPI()


@app.get("/healthcheck")
async def health_check():
    return {"service": "orders", "status": "ok"}
