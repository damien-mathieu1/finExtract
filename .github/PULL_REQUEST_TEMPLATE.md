## Summary

<!-- What changed, in 1-3 bullets. -->

-

## Why

<!-- The problem or motivation. Link an issue if there is one. -->

## Test plan

<!-- Commands run, manual checks done. Be specific (test output, screenshots for UI). -->

- [ ] `uv run pytest` / `uv run ruff check .` / `uv run ruff format --check .` pass
- [ ] `pnpm typecheck` / `pnpm build` pass (if the frontend changed)
- [ ] Checked against the published statement (if parsing or mapping changed)
- [ ] Manually verified in the browser (if user-facing)

## Checklist

- [ ] PR title follows Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`)
- [ ] Alembic migration added (if the schema changed)
- [ ] UI strings added to `en`, `fr` and `ja` (if any)
