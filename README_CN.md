# Coordinate Worktrees

[English](README.md)

跨隔离的 Git worktree 协调用户明确要求的长期 Codex App 研发任务；只有远端评审已获授权时，才通过彼此独立评审的 Pull Request 或 Merge Request 交付，并在不丢失可恢复工作的前提下安全退役已完成通道。

这个技能帮助一个统一协调任务把工作拆分为持久的交付通道，明确分支和评审所有权，并判断哪些工作适合交给短期子智能体，哪些工作需要进入拥有独立 worktree 的用户可见 Codex App 任务。

## 使用要求

- 支持用户可见任务和原生 worktree 的 Codex App
- 用于实现工作的 Git 仓库
- 当工作流包含 PR 或 MR 时，需要 GitHub 或 GitLab 远端仓库

这个技能负责协调 Codex App 已提供的能力，并不会为仅使用 CLI 的环境或其他智能体运行环境增加 worktree 任务支持。Codex CLI 可以安装和读取该技能，但无法执行它依赖的 Codex App 持久任务编排能力。

## 安装

把下面的提示词发送给 Codex：

```text
请使用 $skill-installer，从 https://github.com/emuio/coordinate-worktrees/tree/main/skills/coordinate-worktrees 安装 coordinate-worktrees 技能。
```

安装完成后，该技能会从下一轮 Codex 对话开始可用。

也可以通过内置安装器手动安装：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo emuio/coordinate-worktrees \
  --path skills/coordinate-worktrees
```

## 使用

可以明确要求 Codex 使用这个技能：

```text
请使用 $coordinate-worktrees，把这个功能拆分为多个隔离的 worktree 任务，统一协调评审并报告合并就绪状态；未经我明确授权，不要 push、创建 PR/MR 或 merge。
```

典型场景包括：

- 在两个独立 worktree 中并行实现，并在集成前分别完成评审。
- 把只读架构审查交给子智能体，同时让持久实现留在用户可见任务中。
- 构建有依赖关系的堆叠式 PR 或 MR，后续工作从最新的 integration 分支开始。
- 由主任务担任唯一协调者和合并决策负责人，其他任务负责实现并处理评审意见；只有记录了合并授权时才执行 merge。

## 任务路由模型

| 工作类型 | 执行载体 | Git 所有权 |
| --- | --- | --- |
| 只读调查或独立评审 | 短期 collaboration subagent | 无 |
| 用户明确要求的持久多通道实现 | Codex App 原生 worktree 任务 | 独立分支；只有获授权时才创建 PR/MR |
| 对相同文件或状态的紧密耦合修改 | 单一串行通道 | 单一所有者 |

协调者负责交付图、集成状态、评审决策，以及已获授权时的最终合并。每个实现通道负责自己的分支、commit、检查和评审修复，但不得自行合并。

新建 App 任务默认不置顶；只有用户明确要求时才置顶。协调关系依靠台账、task handle、分支和 PR/MR 维护，而不是依赖侧边栏顺序。

## 动作授权

技能把交付模式与每一项外部动作的授权分开记录：

| 模式 | 默认边界 |
| --- | --- |
| `plan-only` | 只读拆分和拟定台账 |
| `local-delivery` | 用户明确要求的 App 任务、本地分支、commit 和测试 |
| `branch-delivery` | 在 `local-delivery` 基础上，按授权 push 分支，但不创建评审 |
| `review-delivery` | 在 `branch-delivery` 基础上，按明确要求创建 Draft PR/MR |

实现任务和可选 listener 的创建授权彼此独立，分别记录为 `createTasks` 与 `createListener`；两者都不等于允许 push、创建评审、merge、deploy、移动已登记的 base checkout、archive task、删除分支或移除手工 worktree。协调者还会分别记录 `pushBranches`、`openReviews`、`merge`、`deploy`、`syncBaseCheckout`、`archiveTasks`、`deleteBranches` 和 `removeManualWorktrees`；即使只允许 push，也不能据此创建 PR/MR。没有明确来源的动作一律保持 `pending`。

任务创建也可能是异步的。只拿到 `clientThreadId` 等 provisioning handle 时，通道记为 `setup-pending`；不得把它当作真实 `threadId` 使用，也不得声称任务已经就绪。

## Worktree 目录与清理

- 持久的 Codex App 任务使用 App 原生 worktree。物理目录由 App 管理，协调者不得手工删除。
- collaboration subagent 共享协调任务的工作目录，不会也不应额外创建 worktree。
- 手工 worktree 只作为明确的备用方案。统一放在 `${CODEX_HOME:-$HOME/.codex}/manual-worktrees/<repository>/<lane>` 这类专用根目录下，不要在主仓库父目录散落大量同名前缀目录。
- 每个通道在开始前都要记录为 `codex-managed`、`permanent` 或 `coordinator-manual`，并声明合并后的退役策略。

每个通道完成合并或被明确放弃后，即使没有远端 PR/MR，协调者也必须执行退役检查，并向用户输出 **Worktree 清理** 小节。小节要列出准确路径，并分类为 `manual-retired`、`cleanup-ready`、`retained-dirty`、`retained-active`、`retained-blocked`、`app-cleanup-pending`、`app-auto-cleaned-restorable` 或 `permanent-retained`。脏、未合并、证据不确定或仍有任务占用的 worktree 只报告、不删除。

归档 App 任务是一项独立授权。Codex 可能在保存可恢复快照后移除已归档任务的 App-managed worktree，因此协调者必须核验最终的任务和 worktree 状态，不能假定目录会立即删除。永久 worktree 保持不动，handoff 视为迁移而不是清理。

## 模型与推理强度

先选择执行载体，再选择模型和推理强度。使用完整父任务历史的 collaboration subagent 会继承父任务当前设置；新建的实现型 Codex App 任务是独立任务，除非用户明确指定覆盖值，否则使用配置默认值，不继承协调任务的临时设置。

用户也可以明确授权协调者按任务难度自适应选择覆盖值。这个授权只适用于当前 delivery graph，并且每个通道都要记录选择理由；协调者不能把上一个手工启动任务的模型和推理强度当作策略来源。

对于用户自报 Pro 20x 并授权质量偏置路由的场景，机械、重复和高吞吐任务使用 Luna / medium；范围窄、要求明确的低风险实现使用 Terra / medium；普通生产实现与验证使用 Terra / high；主要难点是有边界的理解和判断时使用 Sol / medium；跨模块、架构、安全、协议、数据库、复杂排障或最终集成验收使用 Sol / high；只有极高风险或反复无法收敛的推理才使用 Sol / xhigh。简化判断就是：难在理解用 Sol，难在执行用 Terra，难在吞吐用 Luna。20x 允许质量偏置，但不应把所有 Terra 通道一律替换成 Sol。

该配置建议主协调任务常态使用 Sol / high，仅在例外性的关键决策点使用 xhigh，在持续的确定性收口阶段可使用 medium。协调者可以按已授权策略配置新建 App 任务，但不能自行改变当前协调任务的设置；需要调整时，只能在有意义的阶段边界建议用户手工切换。

跟踪进度时，协调者直接等待最多八个已经就绪的目标，并保留事件 cursor；实现任务始终是权威的 self-notifier。只有用户明确要求新增一个用户可见监听任务时，才创建独立 listener；它只是 best-effort 的只读 observer，不能成为通知、验收、合并或清理的所有者。只有需要完整记录或诊断细节时才使用 `read_thread`，并且不汇报没有变化的快照。

## 安全模型

- 保留用户的 Git identity，并遵守仓库规则。
- 不要把 secret 或 credential 写入提示词、仓库文件、日志或评审描述。
- 把分支和 PR/MR 作为持久的所有权记录；thread ID 仅作为运行时句柄。
- 分别记录任务创建、分支 push、创建评审、merge、deploy、base checkout 移动、任务归档、分支删除与手工 worktree 移除的授权。
- 每次合并后都要报告仍然存在的 worktree，不能让清理责任悄然遗留。

## 许可证

[MIT](LICENSE)
