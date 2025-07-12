import os
import requests
from dotenv import load_dotenv
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Load environment variables
load_dotenv()

HF_TOKEN = os.getenv("HF_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "rag-index"

# Load embedding model
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Connect to Pinecone vectorstore
vectorstore = LangchainPinecone.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embedding_model,
)


def call_huggingface_model(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 300
        }
    }

    response = requests.post(
        "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
        headers=headers,
        json=payload
    )

    try:
        result = response.json()
    except Exception:
        return "I don't know"

    if isinstance(result, dict) and "error" in result:
        return "I don't know"

    if isinstance(result, list) and "summary_text" in result[0]:
        output = result[0]["summary_text"].strip()

        # Handle bad model responses
        if not output or len(output) < 10:
            return "I don't know"
        if output.lower().startswith("answer the question") or output.lower().startswith("context:"):
            return "I don't know"

        return output

    return "I don't know"


def get_rag_response(question: str) -> str:
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
        docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        return "I don't know"

    if not context.strip():
        return "I don't know"

    prompt = f"""Answer the question based only on the context below. If you don't know the answer, say "I don't know".

Context:
{context}

Question: {question}
"""

    return call_huggingface_model(prompt)
