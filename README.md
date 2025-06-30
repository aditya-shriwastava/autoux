# AutoUX
> AI agent that sees your screen and acts with keyboard and mouse.

## Getting Started
1. **Clone the repository**
```bash
git clone https://github.com/aditya-shriwastava/autoux.git
cd autoux
```

2. **Create and activate a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install .
```
Or, for development (with extra tools):
```bash
pip install -e .[dev]
```

4. **Usage**
After installation, you can run AutoUX with:
```bash
autoux
```
This will start the agent.

## Development

### Running Tests
To run the full test suite:
```bash
pytest
```

To run tests with verbose output:
```bash
pytest -v
```

### Code Quality

#### Checking for linting issues:
```bash
ruff check
```

#### Auto-fixing linting issues:
```bash
ruff check --fix
```

#### Code formatting:
```bash
ruff format
```

#### Running all quality checks:
```bash
ruff check && ruff format --check
```