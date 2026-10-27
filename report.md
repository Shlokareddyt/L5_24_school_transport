# Lab 5: Static Code Analysis — Report

**File analyzed:** `school_transport.py`
**Tools used:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1 (pycodestyle 2.15.0, pyflakes 4.0.3)

## Summary of results

| Tool    | Before                                  | After                      |
|---------|------------------------------------------|-----------------------------|
| Pylint  | 4.00 / 10                                | **10.00 / 10**               |
| Bandit  | 4 issues (1 High, 1 Medium, 2 Low)       | **0 issues**                 |
| Flake8  | 8 violations                             | **0 violations**             |

Full before/after output for each tool is in `pylint_report.txt`, `bandit_report.txt`, and
`flake8_report.txt` (current/after versions) and in `reports/*_before.txt` / `reports/*_after.txt`.

## Issue Table

| Issue | Type | Tool | Line(s) | Description | Fix Approach |
|---|---|---|---|---|---|
| SQL injection via f-string | Security (High risk pattern) | Bandit B608 | 9 | `enrollRider` built the `INSERT` statement with an f-string, so any value passed as `student`/`route`/`stop` would be interpolated directly into the SQL text. | Switched to a parameterized query (`?` placeholders with a tuple of values) so the driver escapes the values instead of the code building SQL text. |
| Shell command injection | Security — High severity | Bandit B602 | 24 | `dispatchAlert` called `subprocess.run(... , shell=True)` on a string built by concatenating the `route` argument, so a route value containing shell metacharacters could execute arbitrary shell commands. | Removed the shell call entirely — the function only needs to announce the dispatch, so it now uses `print(f"dispatching bus {route}")`. This also removes the subprocess-import warning (B404) and the later partial-path/no-shell warnings (B603/B607) that appeared when a list-based `subprocess.run` was tried as an intermediate fix. |
| Bare `assert` for a runtime check | Security/Design | Bandit B101, pylint | 38 | `assert feeCollected("R1") == 3600` is removed when Python runs with `-O` (optimized bytecode), so the check would silently disappear in production. | Replaced with an explicit `if total != 3600: raise ValueError(...)`, which always runs regardless of optimization flags. |
| Bare `except:` | Bug / Error handling | Pylint W0702, Flake8 E722 | 30 | `except:` in `feeCollected` catches every exception, including ones unrelated to the database call (e.g. `KeyboardInterrupt`), which can hide real bugs. | Narrowed to `except sqlite3.Error:`, which only catches database-related failures. |
| Non-PEP8 function names | Style | Pylint C0103 | 8, 13, 17, 23, 27 | `enrollRider`, `routeRoster`, `exportRoster`, `dispatchAlert`, `feeCollected` used camelCase instead of Python's snake_case convention. | Renamed to `enroll_rider`, `route_roster`, `export_roster`, `dispatch_alert`, `fee_collected` and updated every call site. |
| Missing docstrings | Style / Maintainability | Pylint C0114, C0116 | 1, 8, 13, 17, 23, 27, 34 | No module or function docstrings, making the script's intent harder to follow for a new reader. | Added a module-level docstring and a one-to-two-line docstring for every function. |
| File opened without context manager / encoding | Resource leak / Portability | Pylint R1732, W1514 | 18 | `exportRoster` used `open(path, "w")` without `with`, risking a leaked file handle on an exception, and without `encoding=`, which makes behavior depend on the OS default encoding. | Rewrote as `with open(path, "w", encoding="utf-8") as out:`. |
| Unused function parameter | Bug-prone / Dead code | Pylint W0613 | 13 | `routeRoster(route, driver)` never used `driver`; the call site even passed `"Mr. Das"` with no effect, which is misleading. | Removed the unused `driver` parameter from `route_roster` and updated the call in `main()` to `route_roster("R2")`. |
| Lines over 79/100 characters | Style (PEP 8) | Flake8 E501, Pylint C0301 | 5, 9, 14, 29 | Several lines exceeded the 79-character PEP 8 limit (up to 116 chars), hurting readability in side-by-side diffs and narrow editors. | Wrapped long SQL strings and expressions across multiple lines. |
| Missing whitespace after commas | Style (PEP 8) | Flake8 E231 | 8 | `enrollRider(student,route,stop,fee)` had no spaces after commas in the parameter list. | Added a space after each comma (`student, route, stop, fee`). |
| Missing blank lines between functions | Style (PEP 8) | Flake8 E302 | 23 | Only one blank line preceded `dispatchAlert` instead of the two PEP 8 requires between top-level functions. | Added a second blank line. |

That is 11 distinct issues fixed (well above the required minimum of four), including every issue Bandit reported, every Flake8 formatting issue, and enough Pylint findings to reach a perfect 10.00/10 score.

## Reflection

**What did static analysis catch that a casual read-through might miss?**
The SQL-injection and shell-injection patterns were easy to miss on a quick read because the code "worked" for the sample data in `main()` — the vulnerability only shows up when an attacker-controlled value reaches those functions. Bandit flagged both immediately by pattern-matching known-dangerous APIs (`shell=True`, f-string-built SQL), which is exactly the kind of systematic check that's hard to do reliably by eye, especially under time pressure.

**How did the three tools complement each other?**
Pylint focused on code quality and maintainability (naming, docstrings, resource handling, unused arguments); Flake8 focused purely on PEP 8 formatting (line length, whitespace, blank lines); Bandit focused only on security-relevant patterns (injection, unsafe use of `subprocess`/`assert`). Running all three gave much broader coverage than any single tool — Pylint and Flake8 overlap a little (e.g. both flag long lines), but Bandit's findings were completely distinct from the other two, which is why "clean" Pylint/Flake8 output alone would not have meant the code was secure.

**Which fixes were highest priority, and why?**
The SQL-injection (Medium/High-risk pattern, B608) and shell-injection (High severity, B602) issues were the top priority because they are directly exploitable: a malicious or malformed `route`/`student` value could execute arbitrary SQL or OS commands. The bare `except:` and the removable `assert` check were next, since they can mask real failures. The remaining items (naming, docstrings, line length, spacing) are quality-of-life and maintainability improvements rather than correctness or security risks, so they were addressed last even though they made up most of the raw issue count.

**How does this change how you'd write code going forward?**
Running Bandit/Pylint/Flake8 (or an equivalent linter) as a normal part of development — ideally in a pre-commit hook or CI step — would catch these patterns before they're ever committed, rather than relying on a manual review pass at the end. In particular, treating `shell=True` and string-built SQL as a hard "stop and rewrite" signal, rather than something to fix later, would avoid reintroducing the two highest-severity issues found here.
