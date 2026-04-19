# Contributing to CloseCheck

Thank you for considering a contribution to CloseCheck! This document outlines guidelines for development, testing, and submitting changes.

---

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Docker & Docker Compose (optional, for containerized development)

### Quick Start

1. **Clone and install dependencies:**
   ```bash
   git clone <repo-url>
   cd closecheck
   make install
   ```

2. **Create a `.env` file in `backend/`:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your ANTHROPIC_API_KEY
   ```

3. **Start development servers:**
   ```bash
   # Terminal 1: Backend
   make dev-backend
   
   # Terminal 2: Frontend
   make dev-frontend
   ```

4. **Open http://localhost:5173** and start testing.

---

## Project Structure

```
closecheck/
├── backend/               FastAPI + rule engine + LLM integration
│   ├── app/
│   │   ├── api/          API routes (v1/)
│   │   ├── rules/        Validation rules (43 rule classes across 7 modules)
│   │   ├── services/     Business logic (parser, classifier, extractor, etc.)
│   │   ├── models/       SQLAlchemy ORM + Pydantic schemas
│   │   ├── llm/          Claude API integration (client.py, prompts.py)
│   │   ├── db/           Database setup
│   │   └── main.py       FastAPI app entry point
│   ├── tests/            Unit + integration + e2e tests
│   ├── requirements.txt   Python dependencies
│   └── pytest.ini         Test configuration
│
├── frontend/              React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/        Three-page flow: Upload → Processing → Report
│   │   ├── api/          Axios client
│   │   └── App.jsx       Root component
│   ├── package.json       npm dependencies
│   └── vite.config.js    Vite build config
│
├── docs/                  Documentation
│   ├── CLAUDE.md         Guidelines for Claude Code / copilot interactions
│   ├── PROJECT.md        Detailed project spec + rule matrix
│   └── CLAUDE_CODE_PROMPTS.md  Step-by-step feature implementation guide
│
├── examples/              Sample closing packages for testing
│   └── Martinez_test/     Real-world example with intentional mismatches
│
├── README.md              Main project documentation
├── CONTRIBUTING.md        This file
├── Makefile               Development commands
└── docker-compose.yml     Docker Compose orchestration

```

---

## Code Style

### Backend (Python)

- **Formatter:** Black (automatic on `make format`)
- **Linter:** Pylint / Ruff (check with `make lint`)
- **Type hints:** Required for function signatures
- **Docstrings:** Google-style docstrings for modules, classes, and public functions
- **Max line length:** 100 characters (Black default)

### Frontend (JavaScript/React)

- **Formatter:** Prettier (automatic on `make format`)
- **Linter:** ESLint (run manually if configured)
- **Framework version:** React 18 (hooks preferred, no class components)
- **State management:** React Router + local state (no Redux for now)

---

## Git Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make atomic commits** with clear messages:
   ```bash
   git commit -m "Add rule PA-008: validate earnest money deposit"
   ```

3. **Push and open a PR** against `main`:
   ```bash
   git push origin feature/my-feature
   ```

4. **Ensure all tests pass:**
   ```bash
   make test-fast
   ```

---

## Testing

### Run All Tests (Mocked)
```bash
make test
```

### Run Unit + Integration Only (Fast)
```bash
make test-fast
```

### Run End-to-End Tests
Requires `ANTHROPIC_API_KEY` and sample docs:
```bash
make test-e2e
```

### Write New Tests

Place tests in `backend/tests/`:
- **Unit tests:** `tests/unit/test_*.py`
- **Integration tests:** `tests/integration/test_*.py`
- **E2E tests:** Tag with `@pytest.mark.e2e`

Example:
```python
import pytest
from app.rules.purchase_agreement import BuyerNameConsistency

@pytest.mark.asyncio
async def test_buyer_name_consistency():
    rule = BuyerNameConsistency()
    result = await rule.check({"purchase_agreement": {"buyer_name": "Jane Doe"}})
    assert result.status == RuleStatus.PASS
```

---

## Adding a Validation Rule

1. **Decide the category:** PA (purchase agreement), TC (title), LN (loan), etc.
2. **Add the rule class** to the appropriate module in `app/rules/`:
   ```python
   from app.rules.base import BaseRule, RuleResult, RuleStatus, Severity
   
   class MyNewRule(BaseRule):
       rule_id = "PA-008"
       category = "purchase_agreement"
       description = "Validate earnest money deposit amount"
       severity = Severity.WARNING
       
       async def check(self, documents: dict) -> RuleResult:
           pa = documents.get("purchase_agreement", {})
           earnest = pa.get("earnest_money_deposit")
           if not earnest:
               return RuleResult(self, RuleStatus.FAIL, "Earnest money not found")
           return RuleResult(self, RuleStatus.PASS)
   ```

3. **Add the rule to the module's `RULES` list** at the bottom of the file.
4. **Write unit tests** in `tests/unit/test_rules.py`.
5. **Test with sample docs:**
   ```bash
   python -m pytest tests/unit/test_rules.py::test_my_new_rule
   ```

---

## Common Commands

| Command | What it does |
|---------|--------------|
| `make install` | Install Python + npm dependencies |
| `make dev-backend` | Start FastAPI dev server (hot reload) |
| `make dev-frontend` | Start Vite dev server (hot reload) |
| `make test` | Run all backend tests |
| `make test-fast` | Run fast tests (skip e2e) |
| `make docker-up` | Build and run services in Docker |
| `make clean` | Remove cache, node_modules, etc. |
| `make clean-db` | Reset database and uploads |

---

## Debugging

### Backend
- **Logs:** Check `backend/` terminal output for `[job_id]` prefixed logs
- **FastAPI docs:** http://localhost:8000/docs
- **Debugger:** Add `import pdb; pdb.set_trace()` or use VS Code debugger

### Frontend
- **DevTools:** Open http://localhost:5173, press F12
- **React DevTools:** Install React DevTools browser extension
- **Network tab:** Check API responses in Network tab

---

## Pull Request Checklist

Before submitting a PR:

- [ ] Code follows the style guide (run `make format`)
- [ ] All tests pass (`make test-fast` or `make test`)
- [ ] No unnecessary dependencies added
- [ ] Commit messages are clear and atomic
- [ ] Documentation updated (README, docstrings, docs/)
- [ ] No hardcoded secrets or API keys

---

## Need Help?

- **Questions:** Open an issue with the `question` label
- **Bug reports:** Open an issue with `bug` label + reproducible steps
- **Feature requests:** Open an issue with `enhancement` label

---

Thank you for contributing! 🚀
