import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import GOOGLE_API_KEY

VECTORSTORE_DIR = 'Vectorstore_db'
KNOWLEDGE_BASE_DIR = 'Knowledge_base'

def build_vectorstore():
    """
    Construye o carga la base de datos vectorial desde los documentos
    en la carpeta knowledge_base.
    """
    print("-- Cargando o Construyendo la base de datos vectorial --")
    
    # Cargar los documentos
    documents = []
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith('.pdf'):
            loader = PyPDFLoader(os.path.join(KNOWLEDGE_BASE_DIR, filename))
            documents.extend(loader.load())
            
    if not documents:
        print("No hay documentos para indexar")
        return None
    
    # Dividir los documentos en fragmentos (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    # Crear embeddings y alamacernar en ChromaDB
    # Los embeddings se convierten de texto a vectores numéricos
    embedding_function = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})
    
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_function,
        persist_directory=VECTORSTORE_DIR
    )
    
    print(f"-- Base de datos vectorial construida con {len(splits)} fragmentos de documentos. --")
    return vectorstore

# Inicializar y contruir la base de datos al iniciar la aplicación
vectorstore = build_vectorstore()

def get_retriever():
    """
    Obtiene un 'retriever' que puede buscar en la base de datos vectorial.
    """
    if vectorstore is None:
        # Si no hay documentos, se crea un retriever "tonto" que no devuelve nada.
        class EmptyRetriever:
            def get_relevant_documents(self, query):
                return []
        return EmptyRetriever()
    return vectorstore.as_retriever(search_kwargs={'k': 3}) # Aquí el k=3 significa que buscará los 3 fragmentos más relevantes