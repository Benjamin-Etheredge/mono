def pip_compile(resolve=None):
    if resolve is None:
        resolve = build_file_dir().name

    run_shell_command(
        name="pip-compile",
        command="uv --python-preference only-system pip compile -U requirements.in --output-file requirements.txt",
        tags=["pip-compile"],
    )

    python_requirements(
        name="requirements",
        resolve=resolve,
    )
    __defaults__(all=dict(resolve=resolve))
