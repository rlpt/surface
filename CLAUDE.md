## Git Workflow

- All work happens on `main` — no feature branches
- Commit frequently with small, logical changes
- Push after every commit (enforced by post-commit hook — auto pull-rebase + push)
- If auto-push fails due to a rebase conflict, attempt to resolve it yourself:
  1. Run `git pull --rebase origin main`
  2. Open each conflicted file, understand both sides, and resolve the conflict markers
  3. `git add` the resolved files, then `git rebase --continue`
  4. Push with `git push origin main`
  5. Only escalate to the human if you cannot confidently resolve the conflict
- Never force push
