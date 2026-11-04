# Contributing to FinExtract

Thanks for helping! FinExtract is a small project, so the process is light.

## Before you start

- **Bug or idea?** Open an issue first, so we can agree on the fix or the feature before you write code.
- **A wrong number in an export?** That counts as a bug. Include the company, the filing and the value you expected.
- **Security issue?** Do not open a public issue; follow [SECURITY.md](SECURITY.md).

## Setup

Requires [uv](https://docs.astral.sh/uv/), Node.js 22, pnpm and Docker.

```bash
cp .env.example .env   # add a Clerk dev key and your SEC User-Agent
docker compose up --build
```

The frontend runs on http://localhost:3000 and the API docs on http://localhost:8000/docs.

You need a free [Clerk](https://clerk.com) dev instance to sign in. EDINET needs a free [API key](https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1); without one, only SEC EDGAR and file upload work.

For backend work only:

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run pytest
```

## Making a change

1. Fork the repo and create a branch from `main`.
2. Keep the change focused: one fix or feature per pull request.
3. Follow the existing style:
   - Domain code stays framework-free: `domain/` defines ports, `infrastructure/` implements them, never the reverse.
   - New XBRL tags go in the tag maps in `src/finextract/mapping/infrastructure/taxonomy_mapper.py`. `docs/xbrl_taxonomy_correspondence.csv` is the reference.
   - Parsing or mapping changes need a test, ideally built from a real filing. Check the values against the published statement.
   - Schema changes need an Alembic migration in `alembic/versions/`.
   - Every UI string goes in `frontend/lib/i18n/locales/` for `en`, `fr` and `ja`. Typecheck fails if a key is missing.
4. Run the checks (the pre-commit hook runs the Python ones too):

   ```bash
   uv run ruff check .
   uv run ruff format .
   uv run pytest
   cd frontend && pnpm typecheck && pnpm build
   ```

5. Commit with [Conventional Commits](https://www.conventionalcommits.org) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`). CI checks it, and the changelog is built from it.
6. Open a pull request and fill in the template. Add screenshots for UI changes.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](../LICENSE).
