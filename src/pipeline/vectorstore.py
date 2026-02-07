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
            self.embedding_model = MistralAIEmbeddings(model="mistral-embed")
            logging.info('Embedding Model ready')
            
        except Exception as e:
            raise CustomException(e,sys)

    
    def logging(self):
        try:
            existing_indexes = self.pc.list_indexes().names()

            if self.index_name not in existing_indexes:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1024,
                    metric="dotproduct",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logging.info("Created Pinecone index")
            else:
                logging.info("Pinecone index already exists")

        except Exception as e:
            raise CustomException(e, sys)

        

    def create_vectorstore(self):
        self.logging()
        
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            
            if stats['total_vector_count'] > 0:
                logging.info(f"Index {self.index_name} already exists and is populated. Loading existing vector store.")
                self.vectorstore = PineconeVectorStore.from_existing_index(
                    index_name=self.index_name,
                    embedding=self.embedding_model,
                    text_key='text'
                )
            else:
                logging.info(f"Index {self.index_name} is empty. Processing documents.")
                obj=ProcessPipeline(directory=self.directory)
                final_doc=obj.start_process()

                self.vectorstore= PineconeVectorStore.from_documents(
                    documents=final_doc,
                    embedding=self.embedding_model,
                    index_name=self.index_name,
                    text_key='text'
                )
                logging.info('vector store created')
        except Exception as e:
            raise CustomException(e, sys)

    
    def create_retriever(self):
        self.create_vectorstore()

        if self.vectorstore is None:
            raise RuntimeError("Vectorstore was not created")

        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 10,
                "fetch_k": 25,
                "lambda_mult": 0.5
            }
        )

        if self.retriever is None:
            raise RuntimeError("Retriever was not created")
        else:
            logging.info('Retriever ready')

        return self.retriever

        