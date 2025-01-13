# Generate Requirements

Requirements are grouped and stored in `3rdparty/python/*.in` files. These are compiled into `requirements.txt` files. These are then consumed by pants to generate lockfiles to insure versions, urls, and hashes are correct.

## Generating Requirements
- `pants pip-compile`
- `pants generate-lockfiles`