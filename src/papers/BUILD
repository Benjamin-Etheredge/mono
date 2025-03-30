python_sources(name="lib")

basic_app(
    entrypoint="app.py",
    docker_image_kwargs=dict(
        extra_run_args=["--network=host"],
        image_tags=["1.0.3"],
    ),
)

basic_app(
    entrypoint="harvest.py",
    target_suffix="-harvest",
    docker_image_kwargs=dict(
        extra_run_args=["--network=host"],
        image_tags=["1.0.7"],
    ),
)
