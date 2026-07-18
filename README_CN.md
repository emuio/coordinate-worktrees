# Coordinate Worktrees

[English](README.md)

跨隔离的 Git worktree 协调长期运行的 Codex App 研发任务，通过经过评审的 Pull Request 或 Merge Request 完成交付，并在不丢失可恢复工作的前提下安全退役已完成通道。

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
请使用 $coordinate-worktrees，把这个功能拆分为多个隔离的 worktree 任务，并统一协调评审和合并。
```

典型场景包括：

- 在两个独立 worktree 中并行实现，并在集成前分别完成评审。
- 把只读架构审查交给子智能体，同时让持久实现留在用户可见任务中。
- 构建有依赖关系的堆叠式 PR 或 MR，后续工作从最新的 integration 分支开始。
- 由主任务担任唯一协调者和合并负责人，其他任务负责实现并处理评审意见。

## 任务路由模型

| 工作类型 | 执行载体 | Git 所有权 |
| --- | --- | --- |
| 只读调查或独立评审 | 短期 collaboration subagent | 无 |
| 需要 commit 和评审的长期实现 | Codex App 原生 worktree 任务 | 独立分支和 PR/MR |
| 对相同文件或状态的紧密耦合修改 | 单一串行通道 | 单一所有者 |

协调者负责交付图、集成状态、评审决策和最终合并。每个实现通道负责自己的分支、commit、检查和评审修复，但不得自行合并。

## 安全模型

- 保留用户的 Git identity，并遵守仓库规则。
- 不要把 secret 或 credential 写入提示词、仓库文件、日志或评审描述。
- 把分支和 PR/MR 作为持久的所有权记录；thread ID 仅作为运行时句柄。
- push、merge、关闭任务及其他外部状态变更都需要明确授权。

## 许可证

[MIT](LICENSE)
