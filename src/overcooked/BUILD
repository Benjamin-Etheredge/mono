pip_compile()

python_sources(name="lib")

basic_app(
    docker_image_kwargs=dict(
        extra_run_args=["--network=host"],
        image_tags=["0.0.1"],
    )
)
