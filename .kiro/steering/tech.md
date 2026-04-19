# Tech Stack

## Language & Runtime
- Python 3 (no specific minimum version pinned)
- Virtual environment via `python3 -m venv .venv`

## Dependencies (`requirements.txt`)
- `pygame >= 2.6.1` — rendering, input, game loop
- `hypothesis >= 6.0.0` — property-based testing
- `pytest >= 7.0.0` — test runner

## Common Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the game
python main.py

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_spell_properties.py -v

# Run tests without watch mode (single pass)
python -m pytest tests/ --tb=short
```

## Testing Approach
- Property-based tests use **Hypothesis** (`@given`, `@settings`, `strategies as st`)
- Tests import modules by inserting the parent directory into `sys.path` — no package install needed
- Mock classes (`MockPlayer`, `MockProjectile`, `MockRect`) are defined per test file to avoid pygame dependency in tests
- Each property test function has a docstring stating which requirement(s) it validates
- `max_examples` is set per test (typically 100–200); statistical tests use `N=500` internal trials
