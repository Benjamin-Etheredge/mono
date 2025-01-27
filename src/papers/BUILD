python_source(
    name="app",
    source="app.py",
)

# Needed for streamlijt
file(name="app-file", source="app.py")

python_source(
    name="harvest",
    source="harvest.py",
)

pex_binary(
    name="binary",
    # entry_point="app.py",
    # dependencies=[":app", "//3rdparty/python:requirements#streamlit"],
    dependencies=[":app"],
    script="streamlit",
    args=[
        "run", 
        "--server.port", "8501", 
        "--server.address", "0.0.0.0", 
        "--server.enableXsrfProtection=false", 
        "--global.developmentMode", "false",
        "src/papers/app.py"],
    # args=["run", "src/papers/app.py"],
    # layout="loose",
    include_tools=True,
    include_requirements=True,
    include_sources=True,
    # layout="packed",
    # execution_mode="venv",
)

docker_image(
    name="img",
    extra_run_args=["--network=host"],
    instructions=[
        "FROM python:3.12-slim",
        "ENV PYTHONUNBUFFERED=1",
        # 'ENTRYPOINT ["ls", "/bin/"]',  # Debugging entrypoint to list contents of /bin/app directory
        'ENTRYPOINT ["/usr/local/bin/python3.12", "/bin/app"]',
        "WORKDIR /bin",
        "COPY src/papers/app.py src/papers/app.py",
        "COPY src.papers/binary.pex /bin/app",
    ],
    image_tags=["1.0.0"],
    dependencies=[
        ":binary",
        ":app-file",
    ],
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
