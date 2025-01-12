run_shell_command(
    name="pip-compile",
    command="uv pip compile -v --output-file=requirements.txt requirements.in",
)

python_requirements(
    name="requirements",
    source="requirements.txt",
)
