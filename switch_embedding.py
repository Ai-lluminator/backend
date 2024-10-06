import chromadb
from chromadb.utils import embedding_functions # This helps us fetch our embedding model
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

chroma_client = chromadb.PersistentClient(path="/home/see/Documents/GitHub/AIlluminator/ai/chromaDB")

# Specify the collection from which you want to extract entries
collection_name = "Green-AI"  # replace with your actual collection name
collection = chroma_client.get_collection(collection_name)

new_client = chromadb.PersistentClient(path="/home/see/Documents/GitHub/AIlluminator/ai/chromaDB_new")
# model = SentenceTransformer("dunzhang/stella_en_400M_v5", trust_remote_code=True).to('mps')
all_docs = collection.get()
new_collection = new_client.get_or_create_collection(
    name=f"Green-AI",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name="Alibaba-NLP/gte-Qwen2-1.5B-instruct", device='cuda', normalize_embeddings=False),
)

with tqdm(total=len(all_docs["documents"])) as pbar:
    for i in range(0, len(all_docs["documents"]), 10):
        new_collection.add(
            documents=all_docs['documents'][i:i+10],
            metadatas=all_docs['metadatas'][i:i+10],
            ids=all_docs['ids'][i:i+10],
        )
        pbar.update(10)