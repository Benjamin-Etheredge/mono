docker_image(
    name="ubuntu",
    source="ci.Dockerfile",
    repository="etheredgeb/github-runner",
    image_tags=["ubuntu", "ubuntu24.04"],
    cache_from=[
        {
            "type": "registry",
            "ref": f"etheredgeb/github-runner:ubuntu24.04-cache",
        }
    ],
    cache_to={
        "type": "registry",
        "ref": f"etheredgeb/github-runner:ubuntu24.04-cache",
    },
)
