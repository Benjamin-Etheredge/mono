python_sources()

pex_binary(
    name="binary",
    entry_point="app.py",
    # Optimal settings for Docker builds
    layout="packed",
    execution_mode="venv",
)

docker_image(
    name="img",
    extra_run_args=["--network=host"],
    instructions=[
        "FROM python:3.12-slim",
        "ENV PYTHONUNBUFFERED=1",
        'ENTRYPOINT ["/usr/local/bin/python3.12", "/bin/app"]',
        "COPY src.papers/binary.pex /bin/app",
    ],
    image_tags=["1.0.0"],
)

pex_binary(
    name="harvest-binary",
    entry_point="harvest.py",
    # Optimal settings for Docker builds
    layout="packed",
    execution_mode="venv",
)

docker_image(
    name="harvest-img",
    extra_run_args=["--network=host"],
    instructions=[
        "FROM python:3.12-slim",
        "ENV PYTHONUNBUFFERED=1",
        'ENTRYPOINT ["/usr/local/bin/python3.12", "/bin/app"]',
        "COPY src.papers/harvest-binary.pex /bin/app",
    ],
    registries=["etheredgeb/papers-harvest"],
    image_tags=["1.0.0"],
)
