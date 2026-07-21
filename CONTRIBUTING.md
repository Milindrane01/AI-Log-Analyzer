# Contributing & Git Strategy

Solo project, but we work as if a team reviews every line — that discipline is the portfolio.

## Branching (GitHub Flow)

- `main` is always deployable. Direct pushes to `main` are forbidden (branch protection once on GitHub).
- Every change: feature branch → Pull Request → CI green → merge (squash).
- Branch names: `<type>/<short-kebab-description>`
  - `feat/log-upload-endpoint`, `fix/jwt-expiry-check`, `docs/architecture-adr-002`, `chore/ci-cache`

Why GitHub Flow and not GitFlow: GitFlow (develop/release/hotfix branches) exists for scheduled
release trains and parallel supported versions. A continuously deployed web service doesn't have
those; the extra branches are pure overhead. Most modern teams use GitHub Flow or trunk-based.

## Conventional Commits

Format: `<type>(<scope>): <imperative summary>`

```
feat(logs): add file upload endpoint with size validation
fix(auth): reject expired refresh tokens
docs(planning): add architecture decision on Celery vs BackgroundTasks
test(parsing): add syslog fixture cases
chore(ci): cache pip dependencies
refactor(ai): extract provider interface
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `ci`.
Why: machine-readable history → automatic changelogs, semantic-release later, and reviewers
(and interviewers reading your history) instantly see intent.

## Pull Request Rules

1. One logical change per PR; keep diffs < ~400 lines where possible.
2. Description: what, why, how tested. Link the milestone/issue.
3. CI must pass: ruff, black --check, mypy, pytest.
4. Update docs and `.env.example` in the same PR as the change that requires them.

## Architecture Decision Records (ADRs)

Significant decisions get a short ADR in `docs/adr/NNN-title.md` (context → decision →
consequences). Module 0 decisions are recorded in the architecture doc; new deviations need an ADR.
