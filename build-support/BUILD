docker_image(
    name="ubuntu",
    source="ci.Dockerfile",
    repository="etheredgeb/github-runner",
    image_tags=["ubuntu24.04"],
    cache_from=[
        {
            "type": "registry",
            "ref": f"etheredgeb/github-runner:ubuntu-cache",
        }
    ],
    cache_to={
        "type": "registry",
        "ref": f"etheredgeb/github-runner:ubuntu-cache",
    },
)