"""
RAG Pipeline
- carga robusta de PDFs (salta corruptos)
- limpieza y normalización
- chunking semántico (o fallback)
- deduplicación por similitud
- creación / llenado de vectorstore (Chroma) opcional
- retriever fusion (similarity + mmr)
- re-ranking ligero (por embeddings o LLM si se inyecta)
- compresión de contexto (usar LLM opcional)
- interfaz simple: build_and_persist_vectorstore(), get_fusion_retriever(), run_rag()
"""

import os
import re
import json
import hashlib
from typing import List, Tuple, Optional

import numpy as np

# LangChain pieces (ajusta imports según versión)
try:
    from langchain_community.document_loaders import PyPDFLoader
except Exception:
    # fallback si instalaste otro loader
    PyPDFLoader = None

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_classic.schema import Document

# Optional experimental semantic chunker
try:
    from langchain_experimental.text_splitter import SemanticChunker
    SEMANTIC_CHUNKER_AVAILABLE = True
except Exception:
    SEMANTIC_CHUNKER_AVAILABLE = False

# -----------------------
# CONFIG (ajusta si quieres)
# -----------------------
KB_DIR = "Knowledge_base"
VECTORSTORE_DIR = "Vectorstore_db"
METADATA_FILE = os.path.join(VECTORSTORE_DIR, "vectorstore_meta.json")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MIN_TEXT_LENGTH = 40
DEDUPE_SIM_THRESHOLD = 0.92

FALLBACK_CHUNK_SIZE = 800
FALLBACK_CHUNK_OVERLAP = 150

# -----------------------
# Utilities
# -----------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    text = text.replace('\t', ' ')
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r'\.{2,}', '.', text)
    return text.strip()

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

# -----------------------
# PDF loading & preprocessing
# -----------------------
def list_pdf_paths(kb_dir: str = KB_DIR) -> List[str]:
    if not os.path.isdir(kb_dir):
        return []
    return [os.path.join(kb_dir, f) for f in sorted(os.listdir(kb_dir)) if f.lower().endswith(".pdf")]

def load_pdfs(pdf_paths: List[str]) -> List[Document]:
    docs: List[Document] = []
    if PyPDFLoader is None:
        raise ImportError("PyPDFLoader no disponible. Instala langchain-community o usa otro loader.")
    for p in pdf_paths:
        try:
            loader = PyPDFLoader(p)
            loaded = loader.load()  # list[Document]
        except Exception as e:
            print(f"[RAG] WARNING: no se pudo cargar {p}: {e}")
            continue
        for d in loaded:
            txt = clean_text(d.page_content)
            if txt and len(txt) >= MIN_TEXT_LENGTH:
                meta = d.metadata or {}
                meta["source"] = meta.get("source", os.path.basename(p))
                docs.append(Document(page_content=txt, metadata=meta))
    return docs

# -----------------------
# Chunking (semantic or fallback)
# -----------------------
def chunk_documents(documents: List[Document], embeddings: HuggingFaceEmbeddings) -> List[Document]:
    if not documents:
        return []
    if SEMANTIC_CHUNKER_AVAILABLE:
        try:
            splitter = SemanticChunker(
                embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=80
            )
            chunks = splitter.split_documents(documents)
            print(f"[RAG] SemanticChunker generado {len(chunks)} chunks")
            return chunks
        except Exception as e:
            print(f"[RAG] SemanticChunker fallo: {e} - usando fallback")
    fallback = RecursiveCharacterTextSplitter(chunk_size=FALLBACK_CHUNK_SIZE, chunk_overlap=FALLBACK_CHUNK_OVERLAP)
    chunks = fallback.split_documents(documents)
    print(f"[RAG] Fallback splitter generado {len(chunks)} chunks")
    return chunks

# -----------------------
# Deduplication by similarity
# -----------------------
def dedupe_by_similarity(docs: List[Document], embeddings: HuggingFaceEmbeddings, threshold: float = DEDUPE_SIM_THRESHOLD) -> List[Document]:
    if not docs:
        return []
    texts = [d.page_content for d in docs]
    vectors = embeddings.embed_documents(texts)
    vecs = [np.array(v, dtype=float) for v in vectors]
    unique = []
    unique_vecs = []
    for i, d in enumerate(docs):
        v = vecs[i]
        dup = False
        for u in unique_vecs:
            if _cosine_sim(v, u) >= threshold:
                dup = True
                break
        if not dup:
            unique.append(d)
            unique_vecs.append(v)
    print(f"[RAG] Deduplicacion: {len(docs)} -> {len(unique)}")
    return unique

# -----------------------
# Build / persist vectorstore (uses pipeline)
# -----------------------
def compute_pdf_hashes(kb_dir: str = KB_DIR) -> dict:
    hashes = {}
    if not os.path.isdir(kb_dir):
        return hashes
    for filename in os.listdir(kb_dir):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(kb_dir, filename)
            with open(path, "rb") as f:
                hashes[filename] = hashlib.md5(f.read()).hexdigest()
    return hashes

def build_and_persist_vectorstore(
    kb_dir: str = KB_DIR,
    vector_dir: str = VECTORSTORE_DIR,
    embedding_model: str = EMBEDDING_MODEL,
    force_rebuild: bool = False
) -> Optional[Chroma]:
    os.makedirs(vector_dir, exist_ok=True)
    current_hashes = compute_pdf_hashes(kb_dir)
    # check existing
    if os.path.exists(vector_dir) and os.path.exists(METADATA_FILE) and not force_rebuild:
        try:
            with open(METADATA_FILE, "r") as f:
                saved = json.load(f)
            if saved == current_hashes:
                print("[RAG] No hay cambios. Cargando vectorstore existente.")
                emb = HuggingFaceEmbeddings(model_name=embedding_model, model_kwargs={"device": "cpu"})
                return Chroma(persist_directory=vector_dir, embedding_function=emb)
            else:
                print("[RAG] Cambios detectados en KB. Reconstruyendo vectorstore.")
        except Exception as e:
            print("[RAG] Warning leyendo metadata:", e)
    # reconstruct
    pdfs = list_pdf_paths(kb_dir)
    docs = load_pdfs(pdfs)
    if not docs:
        print("[RAG] No hay PDFs válidos en KB")
        return None
    emb = HuggingFaceEmbeddings(model_name=embedding_model, model_kwargs={"device": "cpu"})
    chunks = chunk_documents(docs, emb)
    chunks = [d for d in chunks if len(d.page_content.strip()) >= MIN_TEXT_LENGTH]
    chunks = dedupe_by_similarity(chunks, emb, threshold=DEDUPE_SIM_THRESHOLD)
    vs = Chroma.from_documents(documents=chunks, embedding=emb, persist_directory=vector_dir)
    with open(METADATA_FILE, "w") as f:
        json.dump(current_hashes, f, indent=2)
    print(f"[RAG] Vectorstore reconstruido con {len(chunks)} fragments")
    return vs

# -----------------------
# Fusion retriever (similarity + mmr) + simple fusion logic
# -----------------------
def get_fusion_retriever(chroma_vs: Chroma, k_sim: int = 4, k_mmr: int = 3, fetch_k: int = 8):
    """
    Devuelve un objeto con .get_relevant_documents(query) que fusiona:
    - similarity (k_sim)
    - mmr (k_mmr, fetch_k)
    Fusiona y elimina duplicados por contenido.
    """
    sim_retriever = chroma_vs.as_retriever(search_type="similarity", search_kwargs={"k": k_sim})
    mmr_retriever = chroma_vs.as_retriever(search_type="mmr", search_kwargs={"k": k_mmr, "fetch_k": fetch_k})

    class FusionRetriever:
        def get_relevant_documents(self, query: str):
            docs = []
            try:
                docs += sim_retriever.get_relevant_documents(query)
            except Exception as e:
                print("[RAG][FusionRetriever] sim error:", e)
            try:
                docs += mmr_retriever.get_relevant_documents(query)
            except Exception as e:
                print("[RAG][FusionRetriever] mmr error:", e)
            # de-dup by content
            seen = set()
            final = []
            for d in docs:
                text = d.page_content.strip()
                if text in seen:
                    continue
                seen.add(text)
                final.append(d)
            # limit to top 6-8
            return final[:8]
    return FusionRetriever()

# -----------------------
# Lightweight reranker (embeddings-based) and optional LLM-based hook
# -----------------------
def embeddings_rerank(docs: List[Document], query: str, embeddings: HuggingFaceEmbeddings) -> List[Document]:
    if not docs:
        return []
    qvec = np.array(embeddings.embed_query(query), dtype=float)
    doc_vecs = [np.array(v, dtype=float) for v in embeddings.embed_documents([d.page_content for d in docs])]
    scores = [_cosine_sim(qvec, dv) for dv in doc_vecs]
    ranked = [d for _, d in sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)]
    return ranked

# Optional: user can provide an LLM callable that given (query, docs) returns docs ranked.
# It must have signature: fn(query: str, docs: List[Document]) -> List[Document]
# Example: a small chain that scores each doc with an LLM and sorts.

# -----------------------
# Context compressor (simple chain wrapper)
# -----------------------
def compress_context(documents: List[Document], query: str, llm_chain_callable = None, max_chars: int = 2000) -> str:
    """
    Reduce la evidencia en un texto condensado.
    If llm_chain_callable provided, it should accept (query, documents) and return a short summary string.
    Otherwise does a naive concatenation + truncate.
    """
    if not documents:
        return ""

    if llm_chain_callable:
        try:
            return llm_chain_callable(query, documents)
        except Exception as e:
            print("[RAG] Warning: llm_chain_callable error:", e)

    # fallback naive compressor: take first N documents, join, truncate
    texts = []
    for d in documents:
        texts.append(f"- {d.page_content[:600].strip()}")
    joined = "\n".join(texts)
    if len(joined) <= max_chars:
        return joined
    # truncate smartly
    return joined[:max_chars].rsplit("\n", 1)[0] + "\n[...summary truncated]"

# -----------------------
# High-level utility: run a RAG flow for a query
# -----------------------
def run_rag(
    query: str,
    chroma_vs: Chroma,
    embeddings: HuggingFaceEmbeddings,
    reranker_fn = None,
    llm_compressor = None,
    top_k: int = 6
) -> dict:
    """
    Execute the optimized RAG flow:
    1. fusion retriever -> candidates
    2. rerank (embeddings or provided fn)
    3. dedupe small
    4. compress context (optional LLM)
    Returns: { "candidates": [...], "context": "...", "ranked": [...] }
    """
    fusion = get_fusion_retriever(chroma_vs)
    candidates = fusion.get_relevant_documents(query)
    if not candidates:
        return {"candidates": [], "context": "", "ranked": []}

    # rerank
    if reranker_fn:
        ranked = reranker_fn(candidates, query)
    else:
        ranked = embeddings_rerank(candidates, query, embeddings)

    # final dedupe by content prefix
    seen = set()
    final = []
    for d in ranked:
        prefix = d.page_content.strip()[:250]
        if prefix in seen:
            continue
        seen.add(prefix)
        final.append(d)
        if len(final) >= top_k:
            break

    # compress
    context = compress_context(final, query, llm_chain_callable=llm_compressor)

    return {"candidates": candidates, "ranked": final, "context": context}

# -----------------------
# Convenience: build & return (vs, embeddings)
# -----------------------
def build_vectorstore_and_embeddings(
    kb_dir: str = KB_DIR,
    vector_dir: str = VECTORSTORE_DIR,
    embedding_model: str = EMBEDDING_MODEL,
    force_rebuild: bool = False
) -> Tuple[Optional[Chroma], HuggingFaceEmbeddings]:
    vs = build_and_persist_vectorstore(kb_dir, vector_dir, embedding_model, force_rebuild=force_rebuild)
    emb = HuggingFaceEmbeddings(model_name=embedding_model, model_kwargs={"device": "cpu"})
    return vs, emb
