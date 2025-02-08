python_sources()

pex_binary(
    name="binary",
    entry_point="app.py",
    layout="packed",
    execution_mode="venv",
)

docker_image(
    name="img",
    extra_run_args=["--network=host"],
    instructions=[
        "FROM python:3.12-slim",
        "ENV PYTHONUNBUFFERED=1",
        "RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 && apt-get clean",
        'ENTRYPOINT ["/usr/local/bin/python3.12", "/bin/app"]',
        "COPY src.webcam-demo/binary.pex /bin/app",
    ],
    image_tags=["1.0.0"],
    skip_hadolint=True,  # not my code
)
