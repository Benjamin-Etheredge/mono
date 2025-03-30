# https://milvus.io/docs/hdbscan_clustering_with_milvus.md
import hdbscan

# needed for visualization
import kaleido  # noqa: F401
# needed for parquet
import pyarrow  # noqa: F401
import numpy as np
import pandas as pd
import plotly.express as px
from pymilvus import Collection, connections
from umap import UMAP

connections.connect(
    host="milvus.k8s.local",
    port="80",
)
collection = Collection(name="authors")
collection.load()

iterator = collection.query_iterator(
    batch_size=10, expr="id >= 0", output_fields=["id", "vector"]
)

search_params = {
    "metric_type": "COSINE",
    # "metric_type": "L2",
    "params": {"nprobe": 10},
}  # L2 is Euclidean distance

ids = []
dist = {}

embeddings = []

while True:
    batch = iterator.next()
    batch_ids = [data["id"] for data in batch]
    ids.extend(batch_ids)

    query_vectors = [data["vector"] for data in batch]
    embeddings.extend(query_vectors)

    results = collection.search(
        data=query_vectors,
        limit=50,
        anns_field="vector",
        param=search_params,
        output_fields=["id"],
    )
    for i, batch_id in enumerate(batch_ids):
        dist[batch_id] = []
        for result in results[i]:
            dist[batch_id].append((result.id, result.distance))

    if len(batch) == 0:
        break

ids2index = {}

for id in dist:
    ids2index[id] = len(ids2index)

dist_metric = np.full((len(ids), len(ids)), np.inf, dtype=np.float64)

for id in dist:
    for result in dist[id]:
        dist_metric[ids2index[id]][ids2index[result[0]]] = result[1]

h = hdbscan.HDBSCAN(
    min_samples=2, 
    min_cluster_size=2, 
    metric="precomputed"
)
hdb = h.fit(dist_metric)

import plotly.io as pio

pio.renderers.default = "notebook"

umap = UMAP(
    n_components=2, 
    # random_state=42, 
    n_neighbors=15, 
    min_dist=0.1,
    metric="cosine",
    # output_metric="cosine",
)

df_umap: pd.DataFrame = (
    pd.DataFrame(umap.fit_transform(np.array(embeddings)), columns=["x", "y"])
    .assign(cluster=lambda df: hdb.labels_.astype(str))
    .query('cluster != "-1"')
    .sort_values(by="cluster")
)
iterator = collection.query_iterator(
    batch_size=10, expr="id >= 0", output_fields=["id", "text", "author", "title", "idx"]
)

ids = []
authors = []
titles = []
indexes = []

while True:
    batch = iterator.next()
    if len(batch) == 0:
        break
    batch_ids = [data["id"] for data in batch]
    batch_authors = [data["author"] for data in batch]
    batch_titles = [data["title"] for data in batch]
    batch_indexes = [data["idx"] for data in batch]
    ids.extend(batch_ids)
    authors.extend(batch_authors)
    titles.extend(batch_titles)
    indexes.extend(batch_indexes)

# TODO: chunk and check that all chunks group together
show_texts = [titles[i] for i in df_umap.index]
show_authors = [authors[i] for i in df_umap.index]
show_indexes = [indexes[i] for i in df_umap.index]

df_umap["title"] = show_texts
df_umap["author"] = show_authors
df_umap["idx"] = show_indexes
df_umap.to_parquet("src/authors/data/clustered_authors.parquet")
# fig = px.scatter(
#     df_umap, 
#     x="x", 
#     y="y", 
#     color="author", 
#     # color="cluster", 
#     hover_data={
#         "title": True,
#         "author": True,
#         "cluster": True,
#         "idx": True,
#     }
# )
# fig.write_image(
#     "clustered_authors_data.png",
#     width=2000,
#     height=2000,
#     scale=2,
# )
# fig.write_html(
#     "clustered_authors_data.html",
#     include_plotlyjs="cdn",
#     full_html=True,
# )