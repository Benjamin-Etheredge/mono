from ollama import Client
import os
from datetime import datetime
from pathlib import Path
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient

from tqdm import tqdm

DATA_DIR = "src/authors/data"
EMBED_MODEL = "nomic-embed-text:v1.5"
CHUNK_SIZE = 8192

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Set up logging
logger.setLevel(logging.INFO)


def get_ollama_client():
    # return Client(host="http://localhost:11434")
    return Client(host="http://ollama.k8s.local:80")


def get_author_from_path(file_path: Path):
    # Really simply way to grap author from path
    parts = file_path.parts
    for idx, part in enumerate(parts):
        if part == "data":
            return parts[idx + 1]
    raise ValueError(f"Author not found in path: {file_path}")

def get_title_from_path(file_path: Path):
    # Really simply way to grap author from path
    parts = file_path.parts
    last_part = parts[-1]
    if last_part.endswith(".txt"):
        return last_part[:-4]
    raise ValueError(f"Title not found in path: {file_path}")

def load_data(data_dir: str):
    logging.info(f"Loading data from {data_dir}")
    data_path = Path(data_dir)
    data = []
    authors = []
    titles = []
    indexes = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_SIZE // 4,
        length_function=len,
    )

    for file in data_path.glob("**/*.txt"):
        if "ge_data" in str(file) or "ghl_data" in str(file):
            # Skip duplicate data
            continue

        logging.info(f"Loading {file}")
        with open(file) as f:
            text = f.read()
        text_chunks = text_splitter.split_text(text)
        data.extend(text_chunks)
        authors.extend([get_author_from_path(file)] * len(text_chunks))
        titles.extend([get_title_from_path(file)] * len(text_chunks))
        indexes.extend(list(range(len(text_chunks))))

    return data, authors, titles, indexes


if __name__ == "__main__":
    print()
    client = get_ollama_client()
    milvus_client = MilvusClient(uri="http://milvus.k8s.local:80")

    # Load data
    logging.info("Loading data...")
    data, authors, titles, indexes = load_data(DATA_DIR)
    chunked_data = []

    logging.info(f"Loaded {len(data)} documents")
    prefixed_data = ["clustering: " + text for text in data]
    logging.info("Generating embeddings...")

    # Generate embeddings
    response = client.embed(input=prefixed_data, model=EMBED_MODEL)
    embeddings = response.embeddings
    logging.info("Embeddings generated")

    # Save embeddings
    # Create collection if not exists
    collection_name = "authors"

    if milvus_client.has_collection(collection_name):
        logging.info(f"Collection {collection_name} already exists")
        # Drop it
        milvus_client.drop_collection(collection_name)
        logging.info(f"Collection {collection_name} dropped")

    milvus_client.create_collection(
        collection_name=collection_name,
        dimension=len(embeddings[0]),
        index_file_size=1024,
        metric_type="COSINE",
        # metric_type="L2",
    )
    logging.info(f"Collection {collection_name} created")

    logging.info("Inserting data into Milvus...")
    records = [
        {"id": i, "vector": embedding, "author": author, "title": title, "text": text, "idx": idx}
        for i, (embedding, author, title, text, idx) in enumerate(tqdm(zip(embeddings, authors, titles, data, indexes)))
    ]
    milvus_client.insert(collection_name=collection_name, data=records)
    logging.info("Data inserted into Milvus")
    # This log is mostly for dvc to track this stage
    with open("src/authors/data/embedding.log", "w") as f:
        f.write(f"Inserted {len(records)} records into Milvus\n")
        f.write(f"Collection: {collection_name}\n")
        f.write(f"Dimension: {len(embeddings[0])}\n")
        f.write("Metric Type: COSINE\n")
