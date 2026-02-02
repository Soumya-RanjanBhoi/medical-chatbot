from fastapi import FastAPI
from langchain_core.messages import HumanMessage,AIMessage
from langchain_classic.prompts import ChatPromptTemplate,PromptTemplate
from src.helper import template
from langchain_mistralai import ChatMistralAI


app= FastAPI()
llm = ChatMistralAI(model="mistral-large-latest",temperature=0.7,max_retries=2)


@app.post('/query')
async def ask_question(query:str):
    


