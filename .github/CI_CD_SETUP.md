# CI/CD Setup Guide

## What's Configured

Your project now has GitHub Actions CI/CD with:

### Python Backend (`.github/workflows/python-ci.yml`)
- **Triggers**: Push to `main`/`owens/observability`, PRs to `main`
- **Jobs**:
  - **Test**: Runs pytest on all tests
  - **Lint**: Placeholder for code quality checks

### Angular Frontend (`.github/workflows/angular-ci.yml`)
- **Triggers**: Push to `main`/`owens/observability`, PRs to `main`
- **Jobs**:
  - Lint, test (with Chrome headless), production build
  - Uploads build artifacts

## How to Use

### 1. Push to GitHub (First Time Setup)
```bash
git add .github/ pytest.ini
git commit -m "Add CI/CD with GitHub Actions"
git push origin owens/observability
```

### 2. Watch It Run
- Go to GitHub repo → **Actions** tab
- You'll see workflows running automatically
- Green ✓ = passed, Red ✗ = failed

### 3. View Results
Click on any workflow run to see:
- Which tests passed/failed
- Build logs
- Artifacts (Angular build output)

## Next Steps (Optional Improvements)

### Add Code Quality Tools
```bash
# Add linter to dev dependencies
uv add --dev ruff

# Update python-ci.yml lint job to:
# - name: Run linter
#   run: uv run ruff check src/ tests/
```

### Add Type Checking
```bash
uv add --dev mypy

# Add job:
# - name: Type check
#   run: uv run mypy src/
```

### Add Code Coverage
```bash
uv add --dev pytest-cov

# Update test command:
# run: uv run pytest tests/ --cov=src --cov-report=term
```

### Branch Protection
On GitHub:
1. Settings → Branches → Add rule for `main`
2. ✓ Require status checks to pass
3. Select: `test`, `lint`, `build-and-test`
4. ✓ Require branches to be up to date

Now PRs can't merge unless CI passes!

## Troubleshooting

### Tests fail in CI but pass locally?
- CI uses fresh environment (no cached data)
- Check for hardcoded paths or missing dependencies
- Set environment variable in workflow: `SKIP_INTEGRATION_TESTS: "true"`

### Secrets Needed?
For API keys:
1. GitHub repo → Settings → Secrets → Actions
2. Add secret (e.g., `OPENAI_API_KEY`)
3. Reference in workflow:
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## What Happens Now

Every time you:
- **Push code** → CI runs automatically
- **Open PR** → CI checks run, shows status on PR
- **Merge PR** → CI validates before allowing merge

You'll see status badges like: ✓ Python Backend CI passing
