run_shell_command(
    name="pip-compile",
    command="uv --python-preference only-system pip compile -U --output-file=requirements.txt requirements.in",
    tags=["pip-compile"],
)

python_requirements(
    name="requirements",
    source="requirements.txt",
    resolve="default",
    module_mapping={"umap-learn": ["umap"]},
    overrides={
        "transformers": {"dependencies": [":requirements#torch"]},
    },
)
