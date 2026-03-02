from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import pathlib
from routes import router

app = FastAPI()

# mount static files directory so HTML files are available under /static
app.mount("/static", StaticFiles(directory=pathlib.Path(__file__).parent.parent / "frontend"), name="static")

# include all routes
app.include_router(router)
