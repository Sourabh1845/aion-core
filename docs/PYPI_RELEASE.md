# PyPI Release Checklist

Package target: `aion-core==0.8.1`

## Preflight

```powershell
cd C:\Users\SOURABH RANJAN\aion-core
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m aion_core.demo
```

Expected:

```text
Ran 19 tests
OK
Receipt verification: PASS (6 receipt(s), hash-verified)
```

## Build

```powershell
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## Publish To TestPyPI First

```powershell
python -m twine upload --repository testpypi dist/*
```

Then test in a clean environment:

```powershell
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple aion-core
aion-demo
```

## Publish To PyPI

```powershell
python -m twine upload dist/*
```

## GitHub Release Publishing

The repository also includes a GitHub Actions workflow:

```text
.github/workflows/python-publish.yml
```

To use it:

1. Create a PyPI API token.
2. Add it as GitHub repository secret `PYPI_API_TOKEN`.
3. Publish GitHub release `v0.8.1`.
4. The workflow builds and uploads `aion-core` to PyPI.

## After Publish

```powershell
python -m pip install aion-core
aion-demo
aion-receipts --help
aion-guard --help
aion-scan --help
aion-team --help
aion-mcp-firewall --help
```

## Notes

- PyPI publishing needs a PyPI API token.
- Do not paste the token into source files.
- Store the token in your password manager or use Twine's prompt.
