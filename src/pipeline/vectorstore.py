from pinecone import Pinecone,ServerlessSpec
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from src.pipeline.process_pipeline import ProcessPipeline
from src.exception import CustomException
from src.logger import logging
import sys
from langchain_mistralai import MistralAIEmbeddings

class initializePinecone:
    def __init__(self,index_name,directory):

        load_dotenv()


        self.index_name=index_name
        self.directory=directory
        self.vectorstore=None
        self.retreiver=None
        

        try:
            self.pc=Pinecone()
            logging.info('successfully loggined into pinecone')
            self.embedding_model=MistralAIEmbeddings(model='mistral-embbed')
            logging.info('Embedding Model ready')
            
        except Exception as e:
            raise CustomException(e,sys)

    
    def logging(self):
        try:
            if self.index_name not in [i['names'] for i in self.pc.list_names()]:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1024,
                    metric='dotproduct',
                    spec=ServerlessSpec(cloud='aws',region='us-east-1')
                )
                logging.info('Logging Created index in Pinecone')
            else:
                logging.info('index name already exists')
        except Exception as e:
            raise CustomException(e,sys)
        

    def create_vectorstore(self):
        obj=ProcessPipeline(directory=self.directory)

        final_doc=obj.start_process()

        self.logging()

        self.vectorstore= PineconeVectorStore.from_documents(
            documents=final_doc,
            embedding=self.embedding_model,
            index_name=self.index_name,
            text_key='text'
        )

        logging.info('vector store created')

    
    def create_retreiver(self):
        self.create_vectorstore()

        if self.vectorstore is None:
            logging.info('vector store not created successfully')
            raise 

        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                    "k": 5,
                    "fetch_k": 20,
                    "lambda_mult": 0.5
                }
            )
        if self.retreiver is None:
            logging.info('retriever not created successfully')
            raise

        
        return self.retreiver
        