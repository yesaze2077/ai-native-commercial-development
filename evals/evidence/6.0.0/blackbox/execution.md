# 独立前向回答与公开 CLI 黑盒验证

结论：在这套明确审查的合成映射中，所测选择与复用行为符合预期；未观察到误选、漏选或不安全缓存误命中。默认 plan 未执行检查、未创建缓存。未知 untracked、显式 lock/global 输入变化均扩大到 integration 全部 5 条并禁用复用。最后已用公开 CLI 确认 5 条 hot，再紧接着执行 release，6 条全部真实新执行。

发现一个安全侧的复用损失现象：第 10 次调用的 5 个 fingerprint 与第 05 次完全相同，但全部 miss；它发生在保守扩大和 release 执行之后，原因未隔离，未读取实现，未修改 runner。它影响可复用率的解释，不构成所观察到的错误绿色结果。

## 独立性与输入

- 只前向阅读候选 `SKILL.md`、incremental-verification、acceptance-and-evidence、commercial-launch-feedback、experience-design、risk-classification、commercial-quality-gates、observability-release-operations、example profile，以及公开 `--help`。未查看 runner 实现、`tests/test_incremental_verify.py`、behavior contracts/rubric、旧回答的语义内容、既有报告或作者结论。
- 10 个分配请求的完整方案回答在 `../responses/<id>.txt`；它们没有声称执行真实业务。`response-hashes.json` 只绑定这 10 个 ID。回答完成后，一次聚合 hash 的 glob 意外遇到共享目录中 28 个文件并在数量断言停止；未展示或使用其他回答内容，已改为精确分配 ID。
- 候选及输入 SHA-256 在 `source-hashes.json`；结束时重新核对，全部未变。
- 仅在隔离合成 repo 执行，无外网、安装、真实数据、真实服务或生产操作。检查命令使用 canonical Python 绝对路径，root/report 也是实际绝对路径，未使用目录 symlink alias。

## Fixture 与基线


合成 repo：`/Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/incremental-verification-20261112/blackbox-run/repo`。
Git：`git version 2.39.5 (Apple Git-154)`。
初始提交：`84fb4d2f0c9c8feb4bf56941e8d9215d5838fb14`；完整 release 6/6 新执行通过后记录 `validated-integration-initial`。
批次提交：`914cd7ae924e54caf1991fd1774dfd529061ef45`；shared/UI/API/docs 的 integration 5 条证据通过后记录 `validated-integration-batch`。

源码与 profile 最初均已提交；版本快照在 `fixture-initial/`、`fixture-batch/`，每轮 diff/status 保留在同目录。profile 不在忽略目录或 repo 外。缓存使用 runner 默认 `.git/incremental-verify/`，报告与外部 audit 在 repo 外，未作为未知源输入。

图为 `shared → UI`、`shared → API`，docs 独立。配置 4 条 quick（shared/UI/API/docs）、1 条 integration（真实读取 UI/API/shared 并做临时文件保存与独立读取比对）、1 条 release（journey + docs）。每条都真实读取合成源码、执行断言；没有 echo 伪通过、强行 sleep 或人为加大工作量。

已逐条审查 `cache:true`、`hermetic:true`、`runtime_inputs:["runtime/fixture.json"]`。检查代码是显式 input；组件及传递依赖覆盖源文件；全部依赖为本机 Python 标准库与声明的合成文件；无网络/真实服务/时间或随机数影响判断。临时持久化输出在独立临时目录创建并删除。外部 `audit.log` 仅 append 通过的检查 ID，检查绝不读取它，不参与结果判断。该观测副作用仅用于区分真实新执行和复用。审查记录为 `fixture-review.json`；hermetic 声明不构成 OS 沙箱保证。

lockfile 使用显式 `global_paths` 声明，因此本次只证明已审查 lock 配置会扩大，未证明自动识别所有锁文件名称。

## 逐轮实际结果

`remaining` 是 runner 报告的当前受影响后续门槛，并非完整商业验收清单。`external wall` 在外部对整个 runner subprocess 用 perf_counter 测量；`runner elapsed` 为 runner JSON 自报，含其 hash/cache 等成本。

| 调用 | stage | selected | executed | reused | remaining | external wall (s) | runner elapsed (s) |
|---|---|---:|---:|---:|---|---:|---:|
| 00-plan | release | 6 | 0 | 0 | api-quick, docs-quick, journey-integration, release-smoke, shared-quick, ui-quick | 0.141521 | 0.113555 |
| 01-baseline-full | release | 6 | 6 | 0 | 无 | 0.904432 | 0.877002 |
| 02-ui-cold | quick | 1 | 1 | 0 | journey-integration, release-smoke | 0.285440 | 0.258400 |
| 03-ui-hot | quick | 1 | 0 | 1 | journey-integration, release-smoke | 0.187641 | 0.161084 |
| 04-docs-independent | integration | 3 | 2 | 1 | release-smoke | 0.454330 | 0.428115 |
| 05-shared-consumers | integration | 5 | 4 | 1 | release-smoke | 0.642682 | 0.615599 |
| 06-unknown-untracked | integration | 5 | 5 | 0 | release-smoke | 0.826636 | 0.798702 |
| 07-lockfile | integration | 5 | 5 | 0 | release-smoke | 0.739869 | 0.712052 |
| 08-global-config | integration | 5 | 5 | 0 | release-smoke | 0.771328 | 0.744905 |
| 09-release-fresh | release | 6 | 6 | 0 | 无 | 1.013151 | 0.985296 |
| 10-cache-provenance-confirmation | integration | 5 | 5 | 0 | release-smoke | 0.716344 | 0.685948 |
| 11-confirmed-hot | integration | 5 | 0 | 5 | release-smoke | 0.327329 | 0.294054 |
| 12-release-after-hot | release | 6 | 6 | 0 | 无 | 0.855887 | 0.828844 |

共 12 次 `--execute` CLI 调用：原定 9 个实际场景，另补 3 次调用纠正“紧邻 release 前缓存已热”的未证假设。合计 selected 53、真实 check 执行 45、复用 8；外部 audit 记录恰好 45 次真实执行，与每轮报告完全一致。缓存实际避免了 8 次检查调用；其中 3 次属于主场景，5 次属于明确 hot 补证。

执行调用 external subprocess wall 合计 **7.725069s**；runner elapsed 合计 **7.390001s**；runner 自报新执行检查 duration 合计 **3.486396s**。plan 另计 external **0.141521s** / runner **0.113555s**。不混用这些计时，也不把 cache hit 当作零耗时。

## 选择、复用与实际变更说明

1. 00 plan 使用 release 全声明集合但不带 `--execute`：6 条 planned、0 次 audit；`.git` 路径清单前后一致，之前不存在 audit，plan 后也不存在。明确请求的 report 是唯一预期输出；见 `plan-side-effects.json`。
2. 01 全量基线：6 条通过，release 缓存 disabled。仅在通过后记录验证基线。
3. 02 将 UI label 从 Save 改为 Save changes；quick 只选择并真实执行 ui-quick，集成与 release 保持 pending。03 无输入变化复用同 fingerprint，audit 增量 0。
4. 04 额外修改独立 docs 的 title，仍对比初始 integration 基线：选择 UI、docs、journey；UI 复用，docs/journey 新执行。证明不相关 docs 变化未无故失效已通过的 UI scoped evidence。
5. 05 额外修改 shared contract 的 description，仍对比完整累计 diff：共享、UI、API、journey 均新执行；独立 docs 复用。说明 shared 变化传播到两个消费者。此处只是兼容的合成契约变更，不声称检测了真实项目的所有语义变化。
6. 验证通过后提交 UI/docs/shared 批次并记录新 integration 基线。06 创建真正 non-ignored untracked `unmapped/novel.json`：`unmapped_path` 扩大到全部 5 条并禁复用，源码另存 `06-unknown-untracked.input.json`。随后只移除这份本测试创建的临时输入。
7. 07 仅改 lockfile，原因 `global_path:package-lock.json`；08 仅改 global config，原因 `global_path:config/global.json`；每次都是 5 条全新执行、无复用。两次结束均按原字节恢复本合成输入，没有 Git reset/clean。
8. 09 release 在批次 exact revision 上 6 条全新执行，但为了避免未经证实地声称“当时缓存仍热”，随后用公开 CLI 补证：10 使用初始基线选中全部 5 条 integration 范围，5 个 fingerprint 与 05 完全相同，却全部 miss。这个保守 miss 原样保留，未追查实现或修复。
9. 10 的通过结果重新温热了当前输入。11 不改文件、同 baseline/stage，5 条均 reused，audit 增量 0；12 紧接着同状态 release，6 条全部 passed/new execution、所有 cache disabled，无 reused、无 remaining。由此直接支持“热缓存不能跳过 release”结论。

## 证据与限制

`summary.json` 含完整 selected/executed/reused/remaining ID、原因、每轮计时与 argv；`commands.txt` 可直接审阅实际 CLI；`command-ledger.json` 含 Git/CLI argv、cwd、return code、原始 stdout/stderr 和外部 wall。逐轮原始 JSON/stdout、diff/status、audit delta、`raw-check-logs/`、源码快照与 hashes 均保留。`consistency-checks.json` 的独立预期选择与外部 audit 对照全部通过。

未观测到误选、漏选或缓存误命中，仅对这套被审查的合成图负责。最终 repo 工作区无源文件改动。未执行失败/fresh 失效、并发输入突变、缓存篡改、超时/取消、symlink 或网络隔离测试。10 条方案回答对这些场景的解释不是执行证据。

微型单次观察受启动与 hash 开销影响；没有统计抽样，没有与另一版本或真实项目作等价对照，不声称真实项目提速、产品验收或商业上线。
