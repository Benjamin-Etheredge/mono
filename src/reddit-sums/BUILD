python_source(
    name="app",
    source="app.py",
)

# Needed for streamlijt
file(name="app-file", source="app.py")

pex_binary(
    name="bin",
    dependencies=[":app"],
    script="streamlit",
    args=[
        "run",
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",
        "--server.enableXsrfProtection=false",
        "--global.developmentMode",
        "false",
        "src/reddit-sums/app.py",
    ],
    include_tools=True,
    include_requirements=True,
    include_sources=True,
)

docker_image(
    name="img",
    extra_run_args=["--network=host"],
    instructions=[
        "FROM python:3.12-slim",
        "ENV PYTHONUNBUFFERED=1",
        'ENTRYPOINT ["/usr/local/bin/python3.12", "/bin/app"]',
        "WORKDIR /bin",
        "COPY src/reddit-sums/app.py src/reddit-sums/app.py",
        "COPY src.reddit-sums/bin.pex /bin/app",
    ],
    image_tags=["1.0.6"],
    dependencies=[
        ":bin",
        ":app-file",
    ],
)
