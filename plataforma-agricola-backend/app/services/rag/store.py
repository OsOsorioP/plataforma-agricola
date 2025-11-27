"""
VectorStoreService adaptado para usar build_vectorstore_and_embeddings()
desde services.rag.pipeline

Provee:
- instancia global vectorstore_service.vs (Chroma) y embeddings
- get_retriever(k)
- add_documents(documents)
- force_rebuild()
"""

import os
from typing import Optional, List
from langchain_classic.schema import Document

# Importa el helper que construye vectorstore en rag_pipeline
from app.services.rag.pipeline import build_vectorstore_and_embeddings

VECTOR_DIR = "Vectorstore_db"
KB_DIR = "Knowledge_base"
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class VectorStoreService:
    def __init__(self, kb_dir: str = KB_DIR, vector_dir: str = VECTOR_DIR, embedding_model: str = DEFAULT_EMBED_MODEL):
        self.kb_dir = kb_dir
        self.vector_dir = vector_dir
        self.embedding_model = embedding_model

        # Inicializacion: construye o carga vectorstore y embeddings
        self.vs, self.embeddings = build_vectorstore_and_embeddings(kb_dir=self.kb_dir,
                                                                    vector_dir=self.vector_dir,
                                                                    embedding_model=self.embedding_model,
                                                                    force_rebuild=False)

    def get_retriever(self, k: int = 3):
        """
        Devuelve un retriever listo para usar por tus agentes y tools.
        Si no existe VS, retorna un retriever vacío que implementa get_relevant_documents(query).
        """
        if self.vs is None:
            class EmptyRetriever:
                def get_relevant_documents(self, query):
                    return []
            return EmptyRetriever()
        return self.vs.as_retriever(search_kwargs={"k": k})

    def add_documents(self, documents: List[Document], persist: bool = True):
        """
        Agrega documentos (lista de langchain.schema.Document) al vectorstore.
        Útil para indexar nuevos PDFs o contenido manual.
        """
        if self.vs is None:
            raise RuntimeError("Vectorstore no está inicializado. Reconstruye primero con force_rebuild().")

        print(f"[VectorStoreService] Agregando {len(documents)} documentos al vectorstore...")
        self.vs.add_documents(documents)
        if persist:
            try:
                self.vs.persist()
            except Exception as e:
                print("[VectorStoreService] Warning: fallo al persistir:", e)
        print("[VectorStoreService] Documentos añadidos.")

    def force_rebuild(self):
        """
        Fuerza la reconstrucción completa desde la KB (usa build_vectorstore_and_embeddings).
        Útil si agregaste PDFs manualmente y quieres reindexar.
        """
        print("[VectorStoreService] Forzando reconstrucción del vectorstore...")
        self.vs, self.embeddings = build_vectorstore_and_embeddings(kb_dir=self.kb_dir,
                                                                    vector_dir=self.vector_dir,
                                                                    embedding_model=self.embedding_model,
                                                                    force_rebuild=True)
        print("[VectorStoreService] Reconstrucción completa.")

# Instancia global (importar desde otros módulos)
vectorstore_service = VectorStoreService()
