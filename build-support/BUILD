docker_image(
    name="ubuntu",
    source="ci.Dockerfile",
    repository="etheredgeb/gha-ubuntu24.04-py3.12",
    image_tags=["1.0.4"],
    cache_from=[
        {
            "type": "registry",
            "ref": f"etheredgeb/gha-ubuntu24.04-py3.12:cache",
        }
    ],
    cache_to={
        "type": "registry",
        "ref": f"etheredgeb/gha-ubuntu24.04-py3.12:cache",
    },
)
