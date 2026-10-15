# Testing

Use Python 3.10 or later in a clean virtual environment:

```sh
python -m venv .venv
# Activate .venv with the command for your shell.
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest
python -m build
```

The pytest configuration enforces the repository's existing 90% coverage floor. CI covers Python 3.10 and 3.14 on Linux, Windows, and macOS. New feature tests use synthetic input and do not require game files or personal data. Run the full suite before submitting a change; CLI regression tests preserve legacy input/output behavior.
