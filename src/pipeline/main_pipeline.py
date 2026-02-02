from src.pipeline.vectorstore import initializePinecone
from src.logger import logging
from src.exception import CustomException
from src.helper import template
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate 


class MainPipeline(initializePinecone):
    def __init__(self,directory,index_name):
        self.index_name=index_name
        self.directory = directory
        super().__init__(index_name,directory)
        self.retreiver=super().create_retreiver()

        self.llm = ChatMistralAI(model="mistral-large-latest",temperature=0.7,max_retries=2)

        logging.info('llm ready..')
        logging.info('Ready for query')

    def query(self,query):
        pass
