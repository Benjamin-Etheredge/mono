import streamlit as st
import pandas as pd
import plotly.express as px

import plotly.graph_objects as go


@st.cache_resource
def load_data():
    return pd.read_parquet("src/authors/data/clustered_authors.parquet")


@st.cache_resource
def load_fig():
    df = load_data()
    fig = px.scatter(
        df,
        x="x",
        y="y",
        color="author",
        # color="cluster",
        hover_data={
            "title": True,
            "author": True,
            "cluster": True,
            "idx": True,
        },
    )
    return fig


# def main():
st.title("Author Clustering")
st.write("Creater: Ben Etheredge")
st.write("This is a clustering of authors based on their works.")
st.write("This is for my own exploration of the data.")
st.write("""
## Process
1. Load the data
2. Chunk with langchain splitter
3. Embed with Ollama and nomic-embed-text
4. Cluster with HDBSCAN
5. Reduce dimensions with UMAP
6. Visualize with Plotly
""")
fig = load_fig()
st.plotly_chart(fig, use_container_width=False)

if __name__ == "__main__":
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap

        streamlit.web.bootstrap.run(__file__, False, [], {})
