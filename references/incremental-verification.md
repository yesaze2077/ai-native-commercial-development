# Incremental Verification and Reusable Results

## Choose the smallest trustworthy check set

Use when iteration is slowed by repeated verification. Inspect existing project scripts, CI, dependency/coverage maps and native affected/cache tools first. Reuse their maintained graph and input model rather than installing or layering another build system. The bundled helper is an optional local fallback for an explicitly reviewed mapping; it does not infer every dependency from source code.

Maintain `changed paths → owning components → dependent consumers → checks`. Include test definitions, shared API/schema/UI contracts, runtime/install inputs and global configuration. Record who owns the mapping and update it with boundary changes. Validate selection against known changes and occasional full regression; observed misses require a mapping fix and wider verification. An unsupported or stale map cannot justify skipping checks.

Compare the last successful baseline appropriate to the stage with the entire current working state, including staged/unstaged, untracked, renamed and deleted files. Do not compare only the latest commit or advance the integration baseline after a quick subset passed. A missing baseline or selector error is not an empty diff: resolve it or run the known full verification path and report the limit. Keep the mapping in version control; an external, ignored or otherwise unbaselined profile cannot justify narrowed selection or cache reuse. A profile whose content differs from its baseline requires conservative full-stage execution with no reuse.

## Separate feedback stages

| Stage | When | Required behavior |
|---|---|---|
| quick | During a coherent local edit | Narrow affected unit/static/fast checks first. Reuse eligible exact-input evidence; show checks still pending. |
| integration | A functional slice/batch is ready, or changes are combined | Include affected quick and integration/contract/critical-path checks across consumers; verify the combined state. Independent native jobs may run in parallel with isolated resources. |
| release | The exact candidate is being accepted for release | Run all declared stages freshly plus any project/risk-required CI, security, migration, recovery and commercial acceptance. No result-cache shortcut or selection-only result replaces release evidence. |

Classify by speed, scope and risk, not a universal test ratio or time target. Measure actual check/queue time and rework before setting budgets. A budget breach is a signal to investigate or split work, not permission to mark an unrun check passed. Batch related edits, avoid repeating successful checks without relevant changes, and investigate flaky/slow tests instead of retrying indefinitely until green.

Unknown paths, changes to the mapping itself, dependency locks, runtime/build/test configuration or explicitly global paths expand to the entire applicable stage and disable cache reuse. Shared contract changes must include consumers and integration; critical security/payment/schema work still follows R2/R3 gates. A local quick pass leaves integration/release obligations visible.

## Optional local planner and runner

Adapt `assets/test-map.example.json` to actual project paths, dependency edges and existing commands only when such configuration is in scope. Reuse an established profile instead of creating duplicate truth. Planning/audit remains read-only; missing mapping does not prevent a safe targeted fix using existing project commands. Review command profiles as executable code before use, and keep credentials and production actions out of test argv.

```bash
python <skill-dir>/scripts/incremental_verify.py \
  --root <repo> --profile <test-map.json> --base <validated-ref> --stage quick
```

The default returns a plan without creating cache state. This POSIX helper targets macOS/Linux; supply canonical real root/cache/report paths rather than directory symlink aliases. Configure an absolute project interpreter (including the intended virtual-environment entry) or an explicitly audited PATH; shell version-manager setup is not inherited. Add `--execute` for authorized local checks. Select `--stage integration` after the batch, and `--stage release` for all declared checks with fresh execution. `--fresh` bypasses cache for diagnosis. Use `--report <path>` to retain structured reasons, results and timing. No command is run through a shell; the child receives a minimal environment plus explicitly allowlisted variables. This is not OS/network containment or authorization for an external action. Preserve existing protected-CI requirements on the exact revision. Release mode forces fresh invocation of every declared command and bypasses this helper’s result cache; a command that internally uses affected-only selection, last-failed filtering or a native test-result cache must itself be configured to satisfy the project’s full/fresh release policy. The wrapper cannot prove that an arbitrary command actually tests its claimed scope.

## Cache a result only when its inputs are controlled

A cacheable check explicitly opts in and declares a hermetic contract, including runtime inputs (an explicit empty list means reviewed absence of additional file inputs). Include component/dependency files, test/config/runtime input contents, file existence/paths, complete command/profile, executable identity, platform/runtime and hashes of declared environment values. Record the runner implementation/cache schema too. Git commit, file timestamp or command name alone is not a valid key; unrelated component edits should not invalidate a correctly scoped key.

Change selection follows Git tracked and non-ignored untracked files, including tracked files that also match ignore rules. Ordinary ignored dependency trees and generated test outputs do not become unknown source changes. Necessary ignored test/runtime/global inputs must be explicitly declared; avoid overly broad runtime globs that scan an entire dependency tree. For a virtual environment, declare the controlled environment identity and relevant configuration/packages, or disable caching.

Do not cache checks with undeclared dependencies, live external state, time/randomness, flaky behavior or consequential side effects. Lockfile equality alone cannot prove an installed environment is unchanged; include a controlled environment identity and necessary runtime inputs or leave caching disabled. Prefer a native hermetic build/test system when the project already has one.

Only actual successful results with intact evidence are reusable. A hit is `reused`, with the original run/revision/time and matching fingerprint; it is not a newly executed pass. Failed/cancelled/timed-out/oversized-output checks do not create a reusable pass; a fresh failed run invalidates an old success for that input. Missing/corrupt/tampered cache or uncertain inputs cause a real run. If covered inputs change during execution or before the aggregate result closes, do not cache or claim that result validates the current state.

The local cache is trusted local state, not cryptographic proof of execution or reviewer identity. The helper caches results/logs, not build output artifacts, deployment smoke, human visual approval or commercial outcomes. Reports distinguish command execution time from total adapter elapsed time, including hashing/cache overhead. Measure both; a hit avoids a command but is not zero waiting. Full release command invocation remains fresh. After native/project acceptance, use the existing delivery-evidence workflow to record the actual stage without claiming SHIP from a cache or planner result.

## Method basis

- [Paul Hammant: Test Impact Analysis](https://martinfowler.com/articles/rise-test-impact-analysis.html): change-to-test selection and its mapping/coverage limits.
- [Ham Vocke: Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html): fast feedback and the complementary roles of unit, integration, contract and end-to-end checks.
- [Nx affected](https://nx.dev/docs/features/ci-features/affected): change/dependency/input-based scope. Tool commands and defaults evolve; use the installed version's documentation.
- [Bazel hermeticity](https://bazel.build/basics/hermeticity), [Bazel caching](https://bazel.build/remote/caching), [Nx inputs](https://nx.dev/docs/reference/inputs): declared input/environment identity is essential to valid reuse.
- [ISTQB CTFL 4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf), [Martin Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html): risk-based effort, small batches and short feedback loops.

These sources motivate the design; they do not prove this helper's dependency map complete or a productivity gain in an unmeasured project.
