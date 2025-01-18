def multi_stage_macro(entrypoint="app.py"):
    pex_binary(
        name="binary-deps",
        entry_point="app.py",
        layout="packed",
        include_sources=False,
        include_tools=True,
    )

    pex_binary(
        name="binary-srcs",
        entry_point="app.py",
        layout="packed",
        include_requirements=False,
        include_tools=True,
    )
    docker_image(
        name="img-deps",
        repository="app",
        registry=["companyname"],
        image_tags=["deps"],
        skip_push=True,
        instructions=[
            "FROM python:3.10-slim",
            "COPY path.to.here/binary-deps.pex /",
            "RUN PEX_TOOLS=1 /usr/local/bin/python3.10 /binary-deps.pex venv --scope=deps --compile /bin/app",
        ],
    )

    docker_image(
        name="img-srcs",
        repository="app",
        registry=["companyname"],
        image_tags=["srcs"],
        skip_push=True,
        instructions=[
            "FROM python:3.10-slim",
            "COPY path.to.here/binary-srcs.pex /",
            "RUN PEX_TOOLS=1 /usr/local/bin/python3.10 /binary-srcs.pex venv --scope=srcs --compile /bin/app",
        ],
    )

    docker_image(
        name="img",
        dependencies=[":img-srcs", ":img-deps"],
        repository="app",
        instructions=[
            "FROM python:3.10-slim",
            'ENTRYPOINT ["/bin/app/pex"]',
            "COPY --from=companyname/app:deps /bin/app /bin/app",
            "COPY --from=companyname/app:srcs /bin/app /bin/app",
        ],
    )
