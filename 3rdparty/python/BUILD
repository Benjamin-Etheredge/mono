run_shell_command(
    name="pip-compile",
    command="uv pip compile -v --output-file=requirements.txt requirements.in",
    tags=["pip-compile"]
)

python_requirements(
    name="requirements",
    source="requirements.txt",
    resolve="python-default",
    overrides={
        "transformers": {"dependencies": [":requirements#torch"]},
    }
)
