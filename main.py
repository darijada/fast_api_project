from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.home_page import router as home_router
from routes.submit_form import router as submit_form_router


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home_router, tags=["Home"])
app.include_router(submit_form_router, tags=["Submit Form"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
