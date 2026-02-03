from fastapi import FastAPI, Cookie, Response
from typing import Optional
from src.pipeline.main_pipeline import MainPipeline,UserManager
app = FastAPI()

pipeline = MainPipeline(directory="data", index_name="index")
user_manager = UserManager()

@app.post("/start")
def start_session(response: Response):
    user_no = user_manager.new_user()
    response.set_cookie(key="user_no", value=str(user_no), httponly=True)
    return {"user_no": user_no}


@app.post("/chat")
def chat(
    question: str,
    user_no: Optional[str] = Cookie(default=None)):

    if user_no is None:
        return {"error": "Session not started"}

    answer = pipeline.query(
        query=question,
        user_id=int(user_no))
    

    return {"answer": answer}

