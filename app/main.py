from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response
from rich import panel, print

from app.api.router import master_router
from app.worker.tasks import add_log


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print(panel.Panel("Server started..", border_style="green"))
    yield
    print(panel.Panel("Server stopped..", border_style="red"))


app = FastAPI(lifespan=lifespan_handler)

app.include_router(master_router)


@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    # the start time
    start = perf_counter()
    response: Response = await call_next(request)
    end = perf_counter()
    # add the log
    time_taken = round(end - start, 2)
    add_log.delay(
        f"{request.method} {request.url} ({response.status_code}) {time_taken}s")
    return response


@app.get("/")
def root():
    return {"message": "Hello World"}


# RUBBISH DOWN HERE
