# Streamlit app for connecting to milvus and exploring data

import streamlit as st
import pymilvus
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
from pymilvus import utility
import pandas as pd
import numpy as np
import os
import ollama

# Connect to Milvus
@st.cache_resource(ttl=3600)  # Cache connection for 1 hour to avoid repeated connections.
def connect_to_milvus(uri):
    client = pymilvus.connections.connect(uri=MILVUS_URI)
    return client

@st.cache_resource(ttl=3600)  # Cache connection for 1 hour to avoid repeated connections.
def connect_to_ollama(uri):
    return ollama.Client(OLLAMA_URI)

MILVUS_URI = os.getenv('MILVUS_URI', 'http://milvus.k8s.lan:80')
OLLAMA_URI = os.getenv('OLLAMA_URI', 'http://ollama.k8s.lan')
EMBED_MODEL = os.getenv('EMBED_MODEL', 'nomic-embed-text')
GEN_MODEL = os.getenv('GEN_MODEL', 'deepseek-r1:14b')

client_milvus = connect_to_milvus(MILVUS_URI)
client_ollama = connect_to_ollama(OLLAMA_URI)

MAX_RESULTS = os.environ.get('MAX_RESULTS', 10)

RAG_TEMPLATE = """### Task:
Respond to the user query using the provided context, incorporating inline citations in the format [source_id] **only when the <source_id> tag is explicitly provided** in the context.

### Guidelines:
- If you don't know the answer, clearly state that.
- If uncertain, ask the user for clarification.
- Respond in the same language as the user's query.
- If the context is unreadable or of poor quality, inform the user and provide the best possible answer.
- If the answer isn't present in the context but you possess the knowledge, explain this to the user and provide the answer using your own understanding.
- **Only include inline citations using [source_id] when a <source_id> tag is explicitly provided in the context.**  
- Do not cite if the <source_id> tag is not provided in the context.  
- Do not use XML tags in your response.
- Ensure citations are concise and directly related to the information provided.

### Example of Citation:
If the user asks about a specific topic and the information is found in "whitepaper.pdf" with a provided <source_id>, the response should include the citation like so:  
* "According to the study, the proposed method increases efficiency by 20% [whitepaper.pdf]."
If no <source_id> is present, the response should omit the citation.

### Output:
Provide a clear and direct response to the user's query, including inline citations in the format [source_id] only when the <source_id> tag is present in the context.

<context>
{}
</context>

<user_query>
{}
</user_query>
"""

def fill_in_template(query, context):
    return RAG_TEMPLATE.format(context, query)
    # return RAG_TEMPLATE.format(query=query, context=context)


collectction_name = "arxiv_None"

# Load the collection
# TODO how is this connecting to milvus?
col = Collection(collectction_name)


@st.cache_data
def embed_text(text):
    # Embedding function using Ollama
    response = client_ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )
    return np.array(response['embedding'])


def generate_text(prompt):
    # Text generation function using Ollama
    stream = client_ollama.chat(
        model=GEN_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        stream=True,
    )
    for chunk in stream:
        yield chunk['message']['content']


# We don't cache since papers in DB will be updating
def search_papers(query_text, query_field, num_results):
    # Convert the query text to a vector (this is just an example, you would need a proper embedding model)
    query_vector = embed_text(query_text)
    query_vector = np.array([query_vector]).astype(np.float32)  # Ensure the vector is in the correct format
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10}
    }
    results = col.search(
        data=query_vector, 
        anns_field=query_field, 
        param=search_params, 
        output_fields=["title", "summary", "authors", "date"],
        limit=num_results)
    return results


def display_results(results):
    for result in results:
        for i, res in enumerate(result):
            st.write(f"Result {i+1}:")
            st.write(f"ID: {res.id}")
            st.write(f"Distance: {res.distance}")
            st.write("Title:", res.entity.get("title"))
            st.write("Authors:", res.entity.get("authors"))
            st.write("Date:", res.entity.get("date"))
            st.write("Summary:")
            for item in res.entity.get("summary"):  # Assuming summary is a list of strings
                st.write(item)  # Print each item in the summary list
            st.write("---")


def get_context(results):
    context = ""
    for result in results:
        for res in result:
            context += f"Title:\n{res.entity.get('title')}\n"
            context += f"Summary:\n{" \n".join(res.entity.get('summary'))}\n"
            context += f"Authors:\n{" \n".join(res.entity.get('authors'))}\n"
    return context


st.title("arXiv Explorer")
st.write("Author: Ben Etheredge")
st.write("""
Ask questions about papers stored in the ArXiv database.
         
The system will search for relevant papers and answer your questions based on the content of those papers.
""")

sidebar = st.sidebar
sidebar.title("Search Options")
sidebar.markdown("Select your search parameters:")
query_field = sidebar.selectbox("Select field to search:", [field.name for field in col.schema.fields if "embedding" in field.name])
num_results = sidebar.number_input("Number of results to return:", min_value=1, max_value=10, value=3)

query_text = st.text_input("Enter a query text:")
results = None
prompt = None
if query_text:
    results = search_papers(query_text, query_field, num_results)


if results:
    context = get_context(results)
    prompt = fill_in_template(query_text, context)
    
    with st.chat_message("ai"):
        with st.spinner("Generating response..."):
            st.write_stream(generate_text(prompt))
else:
    st.write("No results to generate a response from.")
    
st.write("---")

st.subheader("Implementation Details")

if results:
    with st.expander("Search Results", expanded=False):
        st.subheader("Search Results")  # Add a subheader for clarity
        display_results(results) 

if prompt:
    with st.expander("Prompt", expanded=False):
        st.write(prompt)

with st.expander("Model Info", expanded=False):
    st.write(f"Embedding model: {EMBED_MODEL}")
    st.write(f"Generation model: {GEN_MODEL}")

with st.expander("Milvus Info", expanded=False):
    # Display basic information about the collection
    st.write(f"Collection: {collectction_name}")
    st.write(f"Number of entities: {col.num_entities}")
    st.write("Schema:")
    st.write(col.schema.to_dict())