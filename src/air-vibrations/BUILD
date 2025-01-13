python_sources()

pex_binary(
    name="binary",
    entry_point="app.py",
    # Optimal settings for Docker builds
    layout="packed",
    execution_mode="venv",
)

file(
    name="manifest",
    source="deployment.yaml",
)

docker_image(
    name="img",
    extra_run_args=["--network=host"],
    instructions=[
        "FROM python:3.12-slim",
        'ENTRYPOINT ["/usr/local/bin/python3.12", "/bin/app"]',
        "COPY src.air-vibrations/binary.pex /bin/app",
    ],
    image_tags=["1.0.0"],
)