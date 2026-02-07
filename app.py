from fastapi import FastAPI, Cookie, Response, Body, status
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn

from src.pipeline.main_pipeline import MainPipeline, UserManager

app = FastAPI()

pipeline: Optional[MainPipeline] = None
user_manager: Optional[UserManager] = None



@app.on_event("startup")
def startup():
    global pipeline, user_manager
    pipeline = MainPipeline(directory="data", index_name="medical-chatbot-1")
    user_manager = UserManager()




@app.get("/")
def root():
    return {"message": "Medical chatbot API"}


@app.get("/health")
def check_health():
    return {"message": "API is working well"}


@app.post("/session/start")
def start_session(response: Response):
    if user_manager is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"message": "Service not initialized"}
        )

    user_no = user_manager.new_user()

    response.set_cookie(
        key="user_no",
        value=str(user_no),
        httponly=True,
        samesite="lax"
    )

    return {"user_no": user_no}


@app.post("/chat")
def chat(
    question: str ,
    user_no: Optional[str] = Cookie(default=None)
):
    if pipeline is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"message": "Service not initialized"}
        )

    if user_no is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Session not started"}
        )

    answer = pipeline.query(
        query=question,
        user_id=int(user_no)
    )

    return {"answer": answer}




if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
