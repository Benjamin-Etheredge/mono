def basic_app(
    entrypoint="app.py",
    base_docker_target="//3rdparty/images:python3.12",
    target_suffix="",
    docker_image_kwargs=None,
):
    if docker_image_kwargs is None:
        docker_image_kwargs = dict(extra_run_args=["--network=host"])

    basic_pex(entrypoint, target_suffix)
    multi_stage_docker(base_docker_target, target_suffix, docker_image_kwargs)


def basic_pex(
    entrypoint="app.py",
    target_suffix="",
):
    pex_binary(
        name=f"binary-deps{target_suffix}",
        entry_point=entrypoint,
        layout="packed",
        include_sources=False,
        include_tools=True,
    )

    pex_binary(
        name=f"binary-srcs{target_suffix}",
        entry_point=entrypoint,
        layout="packed",
        include_requirements=False,
        include_tools=True,
    )


def multi_stage_docker(
    base_python_target="//3rdparty/images:python3.12",
    target_suffix="",
    docker_image_kwargs=None,
):
    if docker_image_kwargs is None:
        docker_image_kwargs = {}

    dot_path = ".".join(str(build_file_dir()).split("/"))
    name = build_file_dir().name + target_suffix

    src_name = f"img-srcs{target_suffix}"
    deps_name = f"img-deps{target_suffix}"

    docker_image(
        name=deps_name,
        image_tags=["deps"],
        skip_push=True,
        repository=f"etheredgeb/{name}",
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
            f"ARG PYTHON_IMAGE={base_python_target}",
            "FROM $PYTHON_IMAGE",
            f"COPY {dot_path}/binary-deps{target_suffix}.pex /binary-deps.pex",
            "RUN PEX_TOOLS=1 python /binary-deps.pex venv --scope=deps --compile /bin/app",
        ],
    )

    docker_image(
        name=src_name,
        image_tags=["srcs"],
        skip_push=True,
        repository=f"etheredgeb/{name}",
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
            f"ARG PYTHON_IMAGE={base_python_target}",
            "FROM $PYTHON_IMAGE",
            f"COPY {dot_path}/binary-srcs{target_suffix}.pex /binary-srcs.pex",
            "RUN PEX_TOOLS=1 python /binary-srcs.pex venv --scope=srcs --compile /bin/app",
        ],
    )

    docker_image(
        name=f"img{target_suffix}",
        repository=f"etheredgeb/{name}",
        instructions=[
            f"ARG DEP_IMAGE=:{deps_name}",
            f"ARG SRC_IMAGE=:{src_name}",
            f"ARG PYTHON_IMAGE={base_python_target}",
            # Have to do this FROM stuff for pants to catch the targets
            "FROM $DEP_IMAGE as deps",
            "FROM $SRC_IMAGE as srcs",
            "FROM $PYTHON_IMAGE",
            'ENTRYPOINT ["/bin/app/pex"]',
            "COPY --from=deps /bin/app /bin/app",
            "COPY --from=srcs /bin/app /bin/app",
        ],
        **docker_image_kwargs,
    )
