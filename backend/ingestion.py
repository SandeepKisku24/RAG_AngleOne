import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from pinecone import Pinecone, ServerlessSpec


load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = "rag-index"

# Create index if it doesn't exist
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric='cosine',
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"  # or your Pinecone region
        )
    )

# Load and split documents
pdf_loader = DirectoryLoader("data/pdfs", glob="*.pdf", loader_cls=PyPDFLoader)
text_loader = DirectoryLoader("data/web_content", glob="*.txt", loader_cls=TextLoader)
documents = pdf_loader.load() + text_loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)
print(f"✅ Total chunks: {len(chunks)}")

# Embedding model
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Store in Pinecone via Langchain
LangchainPinecone.from_documents(
    documents=chunks,
    embedding=embedding_model,
    index_name=index_name,
)

print("✅ Data successfully uploaded to Pinecone")
