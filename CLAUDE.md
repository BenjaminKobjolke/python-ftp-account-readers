# Version
3

# Coding Rules (Pointer)

This project's rules live in two files in the project root:

- `CODING_RULES.md` — code quality and conventions. BINDING for all code work in
  this repository, always.
- `IMPLEMENTATION_FLOW.md` — the end-to-end flow to follow when planning and
  implementing a change (checks, gates, Definition of Done).

MANDATORY: Before writing or editing ANY code, you MUST Read BOTH files in full
**in the current session**. Do not rely on memory of a previous session, a
summary, or partial reads.

If you are about to make a code change and have not read both files in this
session: STOP, read them, then continue.

An external tool may orchestrate the implementation itself. When a skill or run
states that the implementation is orchestrated, ignore `IMPLEMENTATION_FLOW.md`
entirely — the orchestrator runs those steps as its own phases. `CODING_RULES.md`
stays binding either way.

Next to `CODING_RULES.md`, apply also writes `CODING_RULES_PLAN.md`,
`CODING_RULES_REVIEW.md` and `CODING_RULES_CODE.md`. When an orchestrator's run
instructions name one of these step files, that file replaces `CODING_RULES.md`
for that run; without such an instruction, `CODING_RULES.md` stays binding in full.

Do not inline rules back into this file and do not use `@import` for either file —
they are intentionally referenced, not imported.

This project's graphify code directory is src/ (scan root; refresh with tools/graphify_update.bat).

## Post-Implementation Code Analysis

After **any** of the following events, you MUST run the changed-file analyzer and fix every reported issue before considering the work complete:

- A new feature has been implemented
- A plan from `claude-plans/` has been finished
- A bug has been fixed

### How to run

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\python-ftp-account-readers'; cmd /c '.\tools\analyze_changed_and_new_files.bat'"
```

This invokes cli-code-analyzer with `--only-changed`, so it reports only on files new or modified vs git `HEAD` (including untracked, excluding deletes).

### When to run the full analyzer instead

Run `tools/analyze_code.bat` (whole tree) instead of the changed-files bat for:
an explicit audit request (`/analyze:run-and-fix`), exception maintenance
(`/analyze:improve-exceptions`), before a release/merge, after refactors that
touch shared code, or when the working tree is clean vs `HEAD` (a changed-files
run would report nothing and silently look "clean").

### Workflow

1. Run the bat above.
2. Read the reports under `code_analysis_results/`. Reports are **per-rule CSV
   files** (one per tool that found issues), e.g. `ruff_analyze.csv`,
   `line_count_report.csv`, `duplicate_code.csv`. **There is no `.md` report.**
   A missing CSV means that rule found nothing. If the folder contains only
   `_violations_cache.db` (no `.csv`/`.txt` files), the run was **clean** — the
   bat also prints a short "No ... violations found" line to stdout in that case.
3. Fix every error and warning that applies to your changes.
4. Re-run until clean. Only then mark the feature / plan / bugfix as done.
   The result cache self-invalidates when source files change. Only on an older
   cli-code-analyzer would you need to delete
   `code_analysis_results/_violations_cache.db` by hand.

If the bat does not exist, run `/analyze:enforce-post-feature-workflow` to install it.
