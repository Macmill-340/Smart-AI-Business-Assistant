from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", encode_kwargs = {"normalize_embeddings": True})
vector_store = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")

def process_document(file_path: str):
    """load pdf, chunk it and save to chromadb"""
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        return "Unsupported file type"
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split = text_splitter.split_documents(docs)

    vector_store.add_documents(documents=split)
    return f"processed {len(split)} chunks from documents"

def retrieve_context(query: str) -> str:
    """search the db based on query"""
    docs = vector_store.similarity_search(query, k=3)
    return "\n\n".join(f"Source: {doc.metadata}\n Content: {doc.page_content}" for doc in docs)
