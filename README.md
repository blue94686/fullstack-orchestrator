# Fullstack Orchestrator

面向 Codex 的通用软件工程编排 Skill。当前版本：`1.4.0-project.40`。

根据任务决定做哪些阶段、由谁执行、允许修改哪里，以及需要什么证据才能结束。支持从 0 到 1 开发，也支持 UI 调整、接口联调、后端修复、功能扩展、只读审查、升级与恢复。小任务直接执行，复杂任务才拆分协作，不要求每次调用全部软件。

## 源码入口

完整源码位于 [`.agents/skills/fullstack-orchestrator/`](.agents/skills/fullstack-orchestrator/)，可以直接浏览、克隆和修改。

| 目录 | 内容 |
| --- | --- |
| [SKILL.md](.agents/skills/fullstack-orchestrator/SKILL.md) | 唯一协调入口、阶段选择和执行规则 |
| [references/](.agents/skills/fullstack-orchestrator/references/) | 任务决策、范围、交接、连接、并发、恢复和验收规范 |
| [scripts/](.agents/skills/fullstack-orchestrator/scripts/) | 任务记录校验、共享目录初始化、本机资源协调及测试 |
| [assets/](.agents/skills/fullstack-orchestrator/assets/) | 任务、接口、数据库迁移和资源映射模板 |
| [agents/openai.yaml](.agents/skills/fullstack-orchestrator/agents/openai.yaml) | Skill 展示配置 |

仓库同时保留版本 ZIP 和 SHA256 完整性清单，便于离线安装和核对。

## 运行逻辑

1. 读取调用项目规则、实际代码、工作区状态及用户目标，确认项目根目录。
2. 判断影响范围，选择模式和必要阶段，明确可写文件、接口与验收标准。
3. 复用适用的已有 Skills；缺少能力时按需发现、审查和验证补充资源。
4. 必要时调用设计或工程执行端，通过有归属的输入、契约和产物交接。
5. Codex 收集实际变更，完成集成、相应测试和差异检查，再报告结果与未验证项。

| 模式 | 用途 |
| --- | --- |
| AUTO | 根据任务选择最小必要流程 |
| GOAL | 持续推进完整目标 |
| PATCH | 局部修复和最小变更 |
| FEATURE | 按依赖增量添加功能 |
| REVIEW | 只读分析，不自动修复 |
| UPGRADE | 升级及兼容性验证 |
| RECOVER | 先核对状态，再按授权恢复 |

## 软件与连接

Codex 统一协调，按任务承担前端、后端、通信、数据库、算法、集成和验收。Stitch 可承担设计；Antigravity、Gemini Desktop、可选的 AI Studio Build 等仅在调用项目允许且实际能力可用时参与。

Gemini 是大模型，Antigravity 与 Gemini Desktop 是不同客户端，CLI、Desktop、MCP 是不同接入方式。安装本 Skill 不会自动建立连接、登录账户或授予文件权限。优先采用任务适用的官方接口和官方 Skills；具体路线服从调用项目规则。

[project-policy.md](.agents/skills/fullstack-orchestrator/references/project-policy.md) 记录的是编写本 Skill 的项目历史偏好，**不作为其他项目的通用默认，也不转移历史授权**。

## 项目隔离与安全边界

- 项目路径动态解析；需要交换文件或恢复记录时，在当前项目创建或复用相对目录 `shared/`。不同项目不共用固定的业务数据目录。窄直接任务和 REVIEW 不强制创建它。
- 按项目和角色复用会话；同一会话执行串行。切换执行端前核对旧任务，运行状态未知时不重复派发。
- 提供最小单机资源协调，容量以本机共同配置为准；GUI 单控制者，项目数据各自保存。它不是分布式调度服务，不提供自动抢占。
- 保留用户已有改动和配置。局部修改仍须检查受影响依赖；产物必须核对项目、任务、尝试与输入版本。
- 生产发布、不可逆数据操作、付费、法律条款确认及扩权遵循对应授权。失败恢复不意味着可以清空用户数据。
- 外部客户端未连接、未获权限或没有实际产物时，明确报告限制；不把文档、校验器通过或 Agent 自述当作业务验收。

## 安装

先把仓库克隆到独立目录，再把其中的 `.agents/skills/fullstack-orchestrator/` 复制到目标项目同名位置。若已有同名 Skill，先比较并备份后决定合并，避免覆盖已有定制。

```bash
git clone https://github.com/blue94686/fullstack-orchestrator.git
```

在目标项目的 Codex 对话中调用：

```text
$fullstack-orchestrator 修复登录表单提交问题，保留现有技术栈和用户改动，按影响范围验证。
```

```text
$fullstack-orchestrator REVIEW：只分析当前 API 的兼容性风险，不修改项目。
```

```text
$fullstack-orchestrator 为现有项目增加收藏功能，先核对权限、接口与数据模型，再按需执行。
```

## 本地检查与验证边界

在本仓库根目录运行辅助脚本测试：

```bash
python3 -m unittest discover -s .agents/skills/fullstack-orchestrator/scripts -p 'test_*.py'
```

脚本测试验证的是辅助逻辑；源码与 ZIP 的完整性核对验证的是文件一致性。二者都不证明所有软件已连通，也不证明任意产品已经通过 E2E、运行中断恢复或生产发布验收。实际项目需按任务收集当前证据。

本仓库只交付可复用 Skill 源码与版本包，不包含业务项目源码、账户凭据、本机容量状态、完整聊天或任务运行记录。
