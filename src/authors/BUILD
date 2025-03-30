python_sources(name="lib")

file(name="df", source="data/clustered_authors.parquet")

basic_app(
    entrypoint="app.py",
    docker_image_kwargs=dict(
        dependencies=[":df"],
        extra_run_args=["--network=host"],
        image_tags=["1.0.0"],
    ),
    extra_instructions=[
        "COPY src/authors/data/clustered_authors.parquet src/authors/data/clustered_authors.parquet",
    ],
)
