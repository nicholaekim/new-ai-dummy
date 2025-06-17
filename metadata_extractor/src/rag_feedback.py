from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from config.settings import CHROMA_DIR, OPENAI_API_KEY

def build_index(pdf_paths: list[str]):
    """Load all text, split, embed, and persist to Chroma."""
    # TODO: implement text loading, splitter, embeddings, Chroma persistence
    pass

def quality_check(extracted: dict) -> dict:
    """Use RetrievalQA over the vectorstore to validate/correct fields."""
    # TODO: load Chroma, setup QA chain, run on each field or full doc
    return extracted
