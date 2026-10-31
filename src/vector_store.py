
import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. LOAD THE EMBEDDING MODEL
# --------------------------------------------------

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


# --------------------------------------------------
# 2. CONNECT TO CHROMADB
# --------------------------------------------------

client = chromadb.PersistentClient(
    path="./database"
)


# Create or access the collection
collection = client.get_or_create_collection(
    name="research_papers",
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# 3. STORE CHUNKS
# --------------------------------------------------

def store_chunks(chunks):
    """
    Convert chunks into embeddings and store them
    in ChromaDB along with their metadata.

    Args:
        chunks: List of chunk dictionaries produced
                by the chunking module.
    """

    if not chunks:
        print("No chunks to store.")
        return

    # Extract text from every chunk
    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    # Generate embeddings in a batch
    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    ).tolist()

    # Extract unique chunk IDs
    ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    # Extract metadata
    metadatas = [
        {
            "paper_id": chunk["paper_id"],
            "paper_title": chunk["paper_title"],
            "section": chunk["section"],
            "page_number": chunk["page_number"]
        }
        for chunk in chunks
    ]

    # Remove previously stored chunks belonging
    # to these papers before re-indexing them.
    paper_ids = list(set(
        chunk["paper_id"]
        for chunk in chunks
    ))

    for paper_id in paper_ids:
        collection.delete(
            where={"paper_id": paper_id}
        )

    # Store embeddings, text and metadata
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Successfully stored {len(chunks)} chunks.")


# --------------------------------------------------
# 4. SEMANTIC SEARCH
# --------------------------------------------------

def search_chunks(query, n_results=5, paper_id=None):
    """
    Find chunks that are semantically similar
    to the user's question.

    Args:
        query: User's research question.
        n_results: Number of results to retrieve.
        paper_id: Optional filter for a particular paper.

    Returns:
        Retrieved documents and metadata.
    """

    # Convert user question into an embedding
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    # Prepare search arguments
    search_args = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count()),
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }

    # Optionally search within one paper
    if paper_id is not None:
        search_args["where"] = {
            "paper_id": paper_id
        }

    # Search ChromaDB
    results = collection.query(**search_args)

    return results
