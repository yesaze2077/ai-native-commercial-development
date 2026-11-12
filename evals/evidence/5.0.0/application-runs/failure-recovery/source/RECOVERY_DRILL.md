# Local synthetic health recovery drill

This fixture is not production. All request records are synthetic. This task is
an R1, bounded localhost exercise: the only planned addition is a repeatable
drill and its instructions; existing application behavior is unchanged.

## Acceptance recorded before implementation

- **FR-1 baseline:** start the supplied app on `127.0.0.1` with an ephemeral
  port and temporary SQLite file. Observe `/health` HTTP 200. Create at least
  one synthetic request through HTTP and verify its returned record by HTTP.
- **FR-2 detect:** stop the baseline process, then start the identical app with
  the same data file and `--fail-health`. Observe `/health` HTTP 503 and retain
  the actual response, instance PID, URL, command, time and code identity.
- **FR-3 recover:** stop the faulty process and restart without the fault flag,
  using that same file. Observe HTTP 200 and verify that the original record
  still exists with identical ID, title and status.
- **FR-4 containment:** clean up every child process and temporary database,
  including on exceptions. No dependency installation, remote network,
  production connection, credentials, schema change or background monitor.
- **FR-5 independent application checks:** execute the supplied read-only
  `verify_http.py` tool against `app.py`. Keep its command and actual output
  alongside drill evidence, outside the commit.

## Verification plan and repeatable command

Run `python3 -B scripts/recovery_drill.py`. The script records exact commands,
runtime/platform, Git revision and source digests in `evidence/recovery.json`.
The default database is temporary, but all three instances share it during
the run. An HTTP 503 must be observed rather than inferred from the flag.

Inspect `evidence/execution.md` for the actual run, external acceptance command,
loaded skill/reference digests and limitations. Evidence, databases and caches
are deliberately not committed. The script refuses non-loopback startup URLs
and disables proxy use for HTTP requests.

Successful completion proves only this deterministic health-flag recovery and
same-file persistence on one local environment. It does not demonstrate a
crash, backup restore, migration rollback, deployment, alerts, production RTO,
capacity, security or commercial outcomes. No human approval, independent
review receipt or production deployment is supplied or inferred. Branch/PR
review and any later release remain separate work.
