import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

VECTORSTORE_DIR = 'Vectorstore_db'
KNOWLEDGE_BASE_DIR = 'Knowledge_base'


def build_vectorstore():
    """
    Construye o carga la base de datos vectorial desde los documentos
    en la carpeta knowledge_base. SOLO reconstruye si los PDFs cambiaron.
    """

    import json
    import hashlib

    METADATA_FILE = "Vectorstore_db/vectorstore_meta.json"

    def compute_pdf_hashes():
        hashes = {}
        for filename in os.listdir(KNOWLEDGE_BASE_DIR):
            if filename.endswith(".pdf"):
                path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
                with open(path, "rb") as f:
                    hashes[filename] = hashlib.md5(f.read()).hexdigest()
        return hashes

    print("-- Cargando o Construyendo la base de datos vectorial --")
    current_hashes = compute_pdf_hashes()

    # ==========================================================
    # 1. Si existe vectorstore + metadata → cargar si no hay cambios
    # ==========================================================
    if os.path.exists(VECTORSTORE_DIR) and os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            saved_hashes = json.load(f)

        if saved_hashes == current_hashes:
            print(
                "-- No hay cambios en los documentos. Cargando vectorstore existente --")

            embedding_function = HuggingFaceEmbeddings(
                model_name='sentence-transformers/all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'}
            )

            return Chroma(
                persist_directory=VECTORSTORE_DIR,
                embedding_function=embedding_function
            )

        else:
            print("-- Cambios detectados en los PDFs. Reconstruyendo vectorstore... --")

    else:
        print(
            "-- No existe vectorstore previo o falta metadata. Construyendo uno nuevo... --")

    # ==========================================================
    # 2. Reconstrucción obligatoria
    # ==========================================================

    documents = []
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith('.pdf'):
            loader = PyPDFLoader(os.path.join(KNOWLEDGE_BASE_DIR, filename))
            documents.extend(loader.load())

    if not documents:
        print("No hay documentos para indexar")
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(documents)

    embedding_function = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2',
        model_kwargs={'device': 'cpu'}
    )

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_function,
        persist_directory=VECTORSTORE_DIR
    )

    # Guardar hashes actualizados
    with open(METADATA_FILE, "w") as f:
        json.dump(current_hashes, f, indent=4)

    print(f"-- Vectorstore reconstruido con {len(splits)} fragmentos --")
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
    # Aquí el k=3 significa que buscará los 3 fragmentos más relevantes
    return vectorstore.as_retriever(search_kwargs={'k': 3})
