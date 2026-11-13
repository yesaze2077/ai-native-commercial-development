# Failure/recovery execution evidence

Result: **passed local synthetic drill**. No production deployment or commercial outcome is verified. This is a bounded exercise, not an actual production incident.

- Branch: `codex/failure-recovery-exercise`
- Exact exercised commit: `80091d4be57f09fc78ed1d64cd65d2e7fb42c9d9`
- Fixture baseline: `5f23801`; `app.py`, `index.html` and the original `.gitignore` are unchanged (`git diff 5f23801 -- app.py index.html .gitignore` produced no output).
- Acceptance and plan recorded before script implementation: `RECOVERY_DRILL.md`, FR-1 through FR-5. R1 assessment is based on isolated localhost, synthetic data, no privileged or external effects and immediate reversibility.
- Python: `3.9.6 (default, Apr 30 2025, 02:07:17)  [Clang 17.0.0 (clang-1700.0.13.5)]`; executable `/Library/Developer/CommandLineTools/usr/bin/python3`.
- Platform: `macOS-26.5.1-arm64-arm-64bit`.
- Run: `2026-11-12T04:03:33.405154+00:00` to `2026-11-12T04:03:33.581821+00:00`; cwd `/Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/application-runs/failure-recovery`.
- Existing untracked `baseline-http.txt` was preserved and was not read or committed.

## Actual commands and observations

1. Baseline before modifications: `python3 -B /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/ai-native-commercial-development/evals/application_cases/verify_http.py /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/application-runs/failure-recovery/app.py` exited 0: 4 tests, 2.539s, OK. This output was observed in the tool session; the pre-existing baseline file was not used.
2. Source check: parse `scripts/recovery_drill.py` with Python `ast.parse`; passed. `git diff --cached --check` passed before commit.
3. Exact-commit drill: `python3 -B scripts/recovery_drill.py` exited 0 with status `passed`; full raw observations are in `recovery.json`.
4. Exact-commit acceptance: `python3 -B /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/ai-native-commercial-development/evals/application_cases/verify_http.py /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/application-runs/failure-recovery/app.py` exited `0`; actual output captured in `http-acceptance.json`:

```text
....
----------------------------------------------------------------------
Ran 4 tests in 2.531s

OK
```

| Instance | Real HTTP request | Observed status | Observed JSON body |
|---|---|---:|---|
| baseline | GET /health | 200 | `{"status": "ok"}` |
| baseline | POST /api/tickets | 201 | `{"id": 1, "title": "Synthetic recovery request", "status": "open"}` |
| baseline | GET /api/tickets?status=all | 200 | `[{"id": 1, "title": "Synthetic recovery request", "status": "open"}]` |
| fault | GET /health | 503 | `{"status": "unhealthy"}` |
| recovered | GET /health | 200 | `{"status": "ok"}` |
| recovered | GET /api/tickets?status=all | 200 | `[{"id": 1, "title": "Synthetic recovery request", "status": "open"}]` |

The baseline created synthetic request ID 1. The baseline process was stopped before the fault process started. The fault was detected from an actual HTTP 503 response, not inferred from its flag. That instance was stopped before the recovered process started without the flag. Every instance used exactly the same temporary SQLite path; recovery returned the original ID/title/status by HTTP GET.

- baseline: PID 30157, http://127.0.0.1:57321; `/Library/Developer/CommandLineTools/usr/bin/python3 -B /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/application-runs/failure-recovery/app.py --data /var/folders/sf/dygzsg196ln6m9jj_xvyxnkm0000gn/T/synthetic-recovery-0z7crwp5/requests.sqlite3 --port 0`.
- fault: PID 30158, http://127.0.0.1:57325; `/Library/Developer/CommandLineTools/usr/bin/python3 -B /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/application-runs/failure-recovery/app.py --data /var/folders/sf/dygzsg196ln6m9jj_xvyxnkm0000gn/T/synthetic-recovery-0z7crwp5/requests.sqlite3 --port 0 --fail-health`.
- recovered: PID 30177, http://127.0.0.1:57328; `/Library/Developer/CommandLineTools/usr/bin/python3 -B /Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/commercial-lifecycle-20261112/application-runs/failure-recovery/app.py --data /var/folders/sf/dygzsg196ln6m9jj_xvyxnkm0000gn/T/synthetic-recovery-0z7crwp5/requests.sqlite3 --port 0`.

Each child was terminated and reaped (return code -15 from deliberate SIGTERM), including the final recovered process. `cleanup.json` independently records that all three PIDs are absent and all three loopback ports closed. The temporary database is absent. No long-running monitor remains.

Observed whole-drill duration was 0.143279 seconds. The measured local restart-to-health interval was 0.049206 seconds; it is not a production RTO or benchmark.

## Source identity and evidence boundary

Loaded candidate files and SHA256 (these hashes were checked after execution; SKILL digest agrees with the initial read):

| File | SHA256 |
|---|---|
| `SKILL.md` | `0ab604cb6c4e07f5cdcd0836726441fcdf9fbc638aca0377167554f8a91f87ac` |
| `references/risk-classification.md` | `f45cc1c18e783234c461bb1a851e509da2786f11adf2d7a6390fc03017141efb` |
| `references/product-discovery.md` | `6bf87ff8c4fda98f8795b4a981eb9a02a3edde4acb9a05cff026c59bbd7fbbaf` |
| `references/experience-design.md` | `a05ab0c80876640d39a742d75184bc709eb899dc62173ab3178fb6d09c5d84da` |
| `references/architecture-and-stack.md` | `4fbe071449266ac0b883b4f2541f28070e240f321ce56273c9fc0f67c286fd4b` |
| `references/operating-model.md` | `fc4a651782f31d79fda48b4b6306ab874b99f9f85e61acf0964195a092a41ede` |
| `references/acceptance-and-evidence.md` | `1bf02b5b493ea8e71cae91e6c3b574ae2f05a843a799165de0f55e96701ab784` |
| `references/commercial-launch-feedback.md` | `40ccf796255e8ce4e8ce41b4b8a2a02a29568334b35b3d8be3df97d0fff0677e` |
| `references/commercial-quality-gates.md` | `4a638b2043fe1f4c5dd93c71aaa7bc20b8b13a2d76e53f10623c59549dd001a8` |
| `references/observability-release-operations.md` | `2954c6f5cfbf6be5563ba20c8f12596424dccbb9cfea7eb990c74bb2b094b1cc` |
| `references/security-and-ai-safety.md` | `7225a7440c669ba414c50d11ba78e4aed6ddc75ad6a3ccd04b23ddaba8cf367d` |

`source-manifest.json` also records assigned input SHA, the eight raw-response digests and acceptance-tool SHA. Responses are independent simulations: no business execution or runtime success is claimed in them. They are not application execution evidence.

Application SHA256: `ef8c56cd0c691ef8752792d5071b371e6e750aba3764b602778544163e5acaeb`.
UI SHA256: `42348e1a3a70cc2d01a9c763ec8d0b7b335eae54f151024b0f1747909af4906a`.
Drill SHA256: `f3de8298793265ed4f7331f225733963733b3430de5dbe7c3ac83a11a43a0954`.

## Limits and next boundary

- Injected health failure only; no crash, disk failure, data corruption, backup restore, migration or real outage was tested. Removing a startup flag is configuration recovery, not database restore.
- HTTP fixture checks and the local recovery path passed. Browser/UI behavior, usability, security, load/capacity, operational alert delivery and production environment remain unverified.
- No dependencies were installed, no network beyond loopback was requested, and no real systems, customer data, secrets, payment or messaging were used.
- No human approval, independent review receipt, PR merge, hosted deployment or launch is fabricated. Local committed work is complete; independent review and any later authorized release are separate prerequisites.
- Commercial demand, activation, revenue, retention and other business outcomes remain unvalidated. Timing/cost comparison with another skill version was not performed, and productivity improvement is not claimed.
- Initial scaffold editing briefly replaced the tracked ignore rules; the focused diff exposed it and the original `.gitignore` was restored before commit. No business-app code changed and the first actual recovery run passed without app fixes.
- Evidence/DB/cache files are not part of the commit. Only the repeatable script and pre-recorded instructions are committed.
