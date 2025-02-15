def basic_app(
    entrypoint="app.py",
    base_docker_target="3rdparty/images:python3.12",
    docker_image_kwargs=None,
):
    if docker_image_kwargs is None:
        docker_image_kwargs = dict(extra_run_args=["--network=host"])

    basic_pex(entrypoint)
    multi_stage_docker(base_docker_target, docker_image_kwargs)


def basic_pex(
        entrypoint="app.py", 
):
    pex_binary(
        name="binary-deps",
        entry_point=entrypoint,
        layout="packed",
        include_sources=False,
        include_tools=True,
    )

    pex_binary(
        name="binary-srcs",
        entry_point=entrypoint,
        layout="packed",
        include_requirements=False,
        include_tools=True,
    )


def multi_stage_docker(
    base_python_target="3rdparty/images:python3.12",
    docker_image_kwargs=None,
):
    if docker_image_kwargs is None:
        docker_image_kwargs = {}

    dot_path = ".".join(str(build_file_dir()).split("/"))
    name = build_file_dir().name

    docker_image(
        name="img-deps",
        image_tags=["deps"],
        skip_push=True,
        cache_from=[
            {
                "type": "registry",
                "ref": f"etheredgeb/{name}:deps",
            }
        ],
        cache_to={
            "type": "registry",
            "ref": f"etheredgeb/{name}:deps",
        },
        instructions=[
            f"ARG BASE_IMAGE={base_python_target}",
            "# hadolint ignore=DL3006",
            "FROM $BASE_IMAGE",
            f"COPY {dot_path}/binary-deps.pex /binary-deps.pex",
            "RUN PEX_TOOLS=1 python /binary-deps.pex venv --scope=deps --compile /bin/app",
        ],
    )

    docker_image(
        name="img-srcs",
        image_tags=["srcs"],
        skip_push=True,
        cache_from=[
            {
                "type": "registry",
                "ref": f"etheredgeb/{name}:srcs",
            }
        ],
        cache_to={
            "type": "registry",
            "ref": f"etheredgeb/{name}:srcs",
        },
        instructions=[
            f"ARG BASE_IMAGE={base_python_target}",
            "# hadolint ignore=DL3006",
            "FROM $BASE_IMAGE",
            f"COPY {dot_path}/binary-srcs.pex /binary-srcs.pex",
            "RUN PEX_TOOLS=1 python /binary-srcs.pex venv --scope=srcs --compile /bin/app",
        ],
    )

    docker_image(
        name="img",
        instructions=[
            "ARG DEP_IMAGE=:img-deps",
            "ARG SRC_IMAGE=:img-srcs",
            f"ARG BASE_IMAGE={base_python_target}",
            # Have to do this FROM stuff for pants to catch the targets
            "# hadolint ignore=DL3006",
            "FROM $DEP_IMAGE as deps",
            "# hadolint ignore=DL3006",
            "FROM $SRC_IMAGE as srcs",
            "# hadolint ignore=DL3006",
            "FROM $BASE_IMAGE",
            'ENTRYPOINT ["/bin/app/pex"]',
            "COPY --from=deps /bin/app /bin/app",
            "COPY --from=srcs /bin/app /bin/app",
        ],
        **docker_image_kwargs,
    )
