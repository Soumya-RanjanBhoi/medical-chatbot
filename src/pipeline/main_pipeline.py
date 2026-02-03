from src.pipeline.vectorstore import initializePinecone
from src.logger import logging
import os,redis
from src.exception import CustomException
from src.helper import template
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate 
from langchain_classic.memory import ConversationSummaryBufferMemory,ConversationBufferMemory
from langchain_classic.chains import LLMChain
from langchain_community.chat_message_histories import RedisChatMessageHistory



class UserManager:
    def __init__(self):
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            raise RuntimeError("REDIS_URL not set")
        self.redis = redis.from_url(redis_url, decode_responses=True)

    def new_user(self) -> int:
        return self.redis.incr("global_user_counter")



class MainPipeline(initializePinecone):
    def __init__(self, directory, index_name):

        load_dotenv()

        if not os.getenv("MISTRAL_API_KEY"):
            raise RuntimeError("MISTRAL_API_KEY  not set")
        
        os.environ["LANGSMITH_TRACING"] = "true" 
        os.environ["LANGSMITH_API_KEY"] = os.environ.get('LANGSMITH_API_KEY',"")

        self.index_name = index_name
        self.directory = directory

        super().__init__(index_name, directory)

        self.retriever = super().create_retriever()
        self.REDIS_URL = os.environ.get("REDIS_URL")
        if not self.REDIS_URL:
            raise RuntimeError("REDIS_URL not set")

        self.llm = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.7,
            max_retries=2
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", template),
            ("system", "{history}"),
            ("human", "Context:\n{context}\n\nQuestion:\n{question}")
        ])

    def extract_req_text(self,query:str): 
        res=self.retriever.invoke(query) 
        req_text=[] 
        for dox in res: 
            req_text.append(dox.page_content) 
        return req_text


    def query(self, query: str, user_id: int):

        message_history = RedisChatMessageHistory(
            url=self.REDIS_URL,
            session_id=f"user_no-{user_id}"
        )

        memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            chat_memory=message_history,
            max_token_limit=1500,
            return_messages=True,
            input_key="question"
        )

        chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_template,
            memory=memory,
            output_key="text"
        )

        context = self.extract_req_text(query)

        resp = chain.invoke({
            "context": context,
            "question": query
        })

        return resp["text"]
