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

| 工作类型 | 执行载体 | 所有权与隔离 |
| --- | --- | --- |
| 一次性调查、消息或证据核对、独立评审 | collaboration subagent | 只读；共享文件系统 |
| 一次性测试、文档或范围明确的修改 | 范围受限的 collaboration subagent | 已授权路径与独占文件归属 |
| 持续开发，需要独立提交和交付 | 用户明确要求或已有明确授权的 Codex App 任务 | 独立 worktree 与分支 |
| 跨阶段或跨日联调，需要单独恢复和交接 | 用户明确要求或已有明确授权的持久 App 任务 | 只读工作可用 projectless；持续时间本身不要求分支 |
| 明确要求的外部消息接收或分流，例如 DWS | 专用 App 任务与已有或获授权的事件后台 | 分别记录任务、事件后台及消息路由授权 |
| 对相同文件或状态的紧密耦合修改 | 单一所有者串行执行 | 复用已有负责人 |

在已授权的协调交付中，先复用已有负责人，再根据任务是交付一次性结果还是需要持续独立负责来选择载体。记录选择、理由、范围、负责路径和完成条件或检查点；模型与推理强度单独判断。这些规则不把普通独立 subagent 工作纳入本技能。外部消息接收与可选的子任务状态观察者是不同职责。

协调者负责交付图、集成状态、评审决策，以及已获授权时的最终合并。每个实现通道负责自己的分支、commit、检查和评审修复，但不得自行合并。

在已有授权内，把耗时实现、测试、持续联调和外部等待交给执行通道或事件机制，让协调窗口保持可响应。协调窗口保留需求、分派、证据审阅、验收及必要的短时或串行核验。每个未完成事项都保留负责人和检查点，在适当节点处理可关联的通知；只有其他已授权工作无法推进时才进行有界事件等待。具体方式见[协调协议](skills/coordinate-worktrees/references/coordinator-control-plane.md)。

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

先选择执行载体，再选择模型和推理强度。使用完整父任务历史的 collaboration subagent 会继承父任务当前设置；新建的实现型 Codex App 任务是独立任务，默认按风险自适应选择模型和推理强度，不继承协调任务或上一个手工启动任务的临时设置。

风险要根据错误后果、权限边界、持久化状态、回滚质量和未解决歧义判断，不能只看任务大小。用户固定值、更高优先级规则或用户明确要求沿用配置默认时，才覆盖自适应流程。每个通道都记录风险、主要难点、模型、推理强度和选择理由。

默认 `sol-6.1-first-adaptive` 配置：范围明确的实现、修复、常规测试与文档使用 GPT-6.1 Sol（`gpt-6.1-sol`）/ medium；复杂设计、排障、集成判断或 elevated 风险使用 GPT-6.1 Sol / high；重大安全或数据风险、弱回滚、持续不收敛的设计问题使用 GPT-6 Astra（`gpt-6-astra`）/ xhigh。推理难度与风险分别判断，不能仅因涉及数据库、部署或文件多就判为 critical。max 和 ultra 不会被自动选择。

总协调推荐长期保持 GPT-6.1 Sol / high；遇到明确的重大风险决策或持续不收敛时，才建议用户手动切到 Astra / xhigh。只有剩余工作进入较长的确定性阶段时才建议 medium，不因短暂步骤或工具等待频繁切档，也不能未经客户端验证就承诺切换保留缓存。用户自报 Pro 20x 只记录为账户背景，不切换另一套路由策略。

核实目标主机支持情况，并记录精确模型 ID。GPT-6.1 Sol 不可用时，使用满足所需推理强度的 Astra；重大风险任务的 Astra 不可用时，使用 GPT-6.1 Sol / xhigh。其他模型选择需要用户明确选择、更高优先级规则，或明确要求节省成本或提高吞吐量。恢复任务时保留已有通道配置及来源，新默认用于新分派任务；可选 listener 仍沿用配置默认。完整规则见 [技能模型路由](skills/coordinate-worktrees/SKILL.md#choose-model-and-reasoning-settings)。

在日常交付中观察结果质量、评审返工和明显等待，把实际问题记录在现有通道报告中，再调整对应任务类型。这是供实际使用检验的默认策略，尚不代表已验证的性能提升。

跟踪进度时，协调者直接等待最多八个已经就绪的目标，并保留事件 cursor；实现任务始终是权威的 self-notifier。只有用户明确要求新增一个用户可见监听任务时，才创建独立 listener；它只是 best-effort 的只读 observer，不能成为通知、验收、合并或清理的所有者。只有需要完整记录或诊断细节时才使用 `read_thread`，并且不汇报没有变化的快照。

## 安全模型

- 保留用户的 Git identity，并遵守仓库规则。
- 不要把 secret 或 credential 写入提示词、仓库文件、日志或评审描述。
- 把分支和 PR/MR 作为持久的所有权记录；thread ID 仅作为运行时句柄。
- 分别记录任务创建、分支 push、创建评审、merge、deploy、base checkout 移动、任务归档、分支删除与手工 worktree 移除的授权。
- 每次合并后都要报告仍然存在的 worktree，不能让清理责任悄然遗留。

## 许可证

[MIT](LICENSE)
