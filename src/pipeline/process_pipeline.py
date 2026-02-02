from langchain_community.document_loaders import DirectoryLoader,PyPDFLoader
from src.exception import CustomException
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from src.logger import logging
import sys
from typing import List
from langchain_classic.schema import Document




class  ProcessPipeline:
    def __init__(self,directory):
        self.dire = directory

    def load_document(self,directory):
        try:
            pdf= DirectoryLoader(
                directory, 
                glob='*.pdf',
                loader_cls=PyPDFLoader
            )

            doc=pdf.load()
            logging.info('document loaded successfully')
            logging.info(f'total pages loaded: {len(doc)}')
            return doc 
        except Exception as e:
            raise CustomException(e,sys)
        
    def extract_useful_text(self,files:List[Document]) -> List:
        filtered_docs=[]
        for doc in files:
            try:
                if hasattr(doc,'page_content') and hasattr(doc,'metadata') and 'source' in doc.metadata and 'page_label' in doc.metadata:
                    cnt= doc.page_content
                    temp=Document(
                        page_content=cnt,
                        metadata={
                            'source':doc.metadata['source'],
                            'page_no':int(doc.metadata['page_label'])
                        }
                    )
                    filtered_docs.append(temp)
            
            except Exception as e:
                raise CustomException(e,sys)
            
        logging.info('Completed extraction of page_content & source')
        logging.info(f'total document created: {len(filtered_docs)}')
        return filtered_docs
    
    def split_text(self,doc:List[Document]):
        try:
            text_splitter= RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=200
            )

            text=text_splitter.split_documents(doc)
            logging.info('Splitting completed')
            logging.info(f'total chunks: {len(text)}')
            return text
        
        except Exception as e:
            raise CustomException(e,sys)
        
    
    def start_process(self):
        logging.info('Starting to  Process the document')
        document=self.load_document(self.dire)
        useful_text=self.extract_useful_text(document)
        final_doc=self.split_text(useful_text)

        logging.info('Chunking Completed , Ready for Indexing')

        return final_doc





        
            

