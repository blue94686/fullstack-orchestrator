# 单机多项目资源协调

适用于同一台机器、同一 OS 用户下，共用本协调器的多个 Codex Main。项目继续各自决定任务、维护契约及验收；协调器只原子分配必要资源，不派发任务。无守护服务、数据库、后台唤醒、自动抢占、分布式锁或生产发布。不同 OS 用户、不同 state 目录、旧版 Skill 和未接入软件不受此机制约束；不得据此声称整台机器的一切执行已被强制限制。

## 身份和存储

使用本 Skill 的 `scripts/local_resources.py`，通过实际 Skill 位置调用，不要求复制到每个产品目录。新状态默认整机四个开发名额、每项目两个；已有状态保留原容量，不在升级时静默改成四个。实际运行容量只认本机共享状态，项目文档仅记录授权偏好，首次执行核对差异后按适用授权 configure。任务数不受开发名额限制，等待、分析和运行分别记录；增加容量不证明外部客户端支持并行。默认协调目录是当前用户 `~/.codex/fullstack-orchestrator/resources`，用于所有参与项目；它是本机资源元数据，不是公共源码交换目录。`--state-dir` 是子命令前的全局选项，仅用于隔离测试；实际协作必须共同使用默认目录，不能通过另选目录绕过占用。acquire 或获准 configure 可初始化目录；status、diagnose 不初始化。状态 JSON 各层重复键、非有限或溢出时间戳均视为损坏并返回结构化 ERROR，保留原状态字节；所有读取和变更操作共同执行此门禁。状态损坏、权限或最终协调目录/文件链接异常时停止相关动作，不覆盖、删除或重新初始化现场。脚本不将所有祖先目录符号链接视为错误（macOS 系统路径可能使用链接）；Main 核对实际存储归属，不把它当成对恶意同用户进程的文件系统防护。

项目输入、提示词、契约、源码、产物、外部定位和验收仍留在所属项目原生记录或根相对 `shared/`。本机状态仅存规范化项目根、coordinator/task/attempt/operation、资源、分配代次和必要时间等控制元数据，不存账号凭证、对话正文或源码。默认目录由脚本创建为私有；同一用户下它不是安全隔离边界。授权令牌用于防止误释放，不构成对恶意同用户进程的认证。

项目显示名称不是唯一身份。先按 execution-boundaries.md 解析产品根和实际执行目录；脚本对根和工作区解析真实路径，处理符号链接别名。目录移动、复制、删除重建及不同挂载点需要 Main 重新核对活动记录，不能把新路径当成已停止的旧任务。现有目录按文件系统实际保存的名称绑定，消除大小写/Unicode 别名，不无条件转小写；历史工作区和项目路径在可观察时也按同一身份比较。路径消失时保留原分配并保守核对，不因重建或移动推断旧执行停止。目录身份依赖当前文件系统观察，不是对路径替换的 OS 写屏障。项目及任务身份必须在调用方记录中稳定，不能通过改 task ID 或 coordinator ID 再发一份同一工作。

## 资源和容量

| 资源 | 规则 |
|---|---|
| 开发容量 | 所有参与项目共用状态中的 development_limit 名额（可配置，支持三个以上执行者）；每个实际活跃开发执行者各持一份，Main 亲自开发也计入。纯协调和只读分析不占名额。每项目上限同样由共享状态中的 project_limit/project_limits 强制检查（新状态默认两个）；明确项目例外后可配置，整机总量仍优先约束 |
| GUI | 同一用户桌面一个控制者，覆盖观察、目标核对、操作和回读，不仅是点击。人工正在操作时让出并核对，不抢焦点 |
| 可写工作区 | 共享 checkout 默认用规范化工作区独占；真正隔离 worktree 可分别申请，仍核对共享契约、迁移、Git 和运行资源 |
| 客户端执行 | 用固定资源键绑定实际客户端/会话；能力未验证可并行时，保守地独占客户端工程执行，不能只锁某条聊天 |
| 其他共享目标 | 端口、Compose 项目/卷、测试数据库、Redis/队列、浏览器 profile、远端环境等按真实目标使用共同资源键；不存密钥或含凭证 URL |

采用 `--development`、`--gui`、`--write-workspace` 与重复 `--resource` 声明需要的资源。一次申请全有或全无；冲突返回后不占住部分资源等待其他资源。自定义资源键必须有 `exclusive:` 前缀并沿用参与项目约定的命名，由下节 resource_identity.py 生成；手写别名与生成键不会自动识别成同一目标，不在活动分配中混用新旧键。可写工作区比较规范化路径及父子重叠，不只比较目录名称；优先声明完整执行 checkout，不能通过仅填某个子目录规避真实写入范围。协调器不扫描所有服务，也不代替端口实际绑定或数据库权限。

## 使用顺序

1. Main 解析项目与基线，核对旧任务/attempt、实际外部执行及副作用，选取最小必要资源。当前可执行代码哈希按 skill-discovery.md 记录；其他项目启动前必须实际读取支持此协议的 Skill，不能宣称全局缓存已更新。
2. `acquire` 提供 `--project-root`、`--coordinator`、`--task`、`--attempt` 和 `--operation`，加上适用资源。每个实际执行者使用稳定且不同的 operation，例如 `execution:main`、`execution:frontend-worker`，各自申请 `--development`；同身份重试是恢复原分配，不能给另一个执行者共用名额。GUI 另用 `gui:submit-frontend` 等稳定短操作身份。脚本不能辨认同名调用背后是否有两个执行者，不能靠改 operation 重复派发同一工作。冲突只延迟依赖动作，保留 READY 等执行状态，在原生记录说明等待原因；继续独立工作，不忙轮询。
3. 成功后把返回令牌及代次绑定到本项目任务记录，勿放入跨项目状态日志或提示词。同身份同资源重试可核对原分配，不能据此再次提交外部任务。提交不确定仍按 UNKNOWN_EXECUTION 核对。
4. 对受控副作用和集成前执行 `check`，并核对原 attempt、输入及候选身份。协调器核对的是活动授权，不是外部执行终态或写入沙箱。
5. `release` 必须提供该分配的令牌、显式确认和简短非秘密证据。GUI 释放表示本次界面操作结束；开发名额和客户端资源只有在对应执行（含仍占用它们的子进程）确认停止且副作用已核对后才可释放。工作区资源只有在全部覆盖路径不再被原执行使用且关闭写入有证据时才可释放；一个交付子目录关闭写入只允许收集该集合。一个 bundle 内任一资源仍在使用或状态未知，就保留整个 bundle；当前脚本不支持部分释放，不能 release 后重取剩余资源制造空窗。证据是调用方声明，脚本不能独立证明其真实性。

GUI 短操作可独立申请和释放；后台执行继续保留开发、客户端及写入资源。只有确认切换会话/目录不影响旧任务且客户端支持安全并行时，才缩小客户端独占范围。不要持有 GUI 等待长时间生成、配额或其他资源；若客户端必须保持前台才能安全执行，则相应占用持续到安全节点。

命令参数以 `python3 <实际Skill路径>/scripts/local_resources.py --help` 和各子命令 `--help` 为准；结构化 JSON 结果用于原生任务记录。退出码 `0` 成功，`2` 表示资源或短事务忙碌（不能派发），`1` 表示错误需核对。有有限等待顺序，无自动派发或唤醒：资源释放后，由仍在运行的 Main 在合理检查点重试；对话停止后不能承诺后台推进。见下节等待策略。

例如 Main 已解析产品根 `product_root`、实际工作区 `execution_workspace` 及脚本位置 `coordinator_script` 后，可用以下模板。变量由当前会话提供，不能从别的项目原样继承；不将令牌写进可提交源码：

```sh
python3 "$coordinator_script" acquire --project-root "$product_root" \
  --coordinator "$coordinator_id" --task "$task_id" --attempt "$attempt_id" \
  --operation execution:frontend-worker --development \
  --write-workspace "$execution_workspace" \
  --resource "$client_resource_key"
python3 "$coordinator_script" check --token="$grant_token"
python3 "$coordinator_script" release --token="$grant_token" \
  --confirmed --evidence 'Confirmed assigned execution stopped; workspace writes closed'
```

最后一条仅在证据成立时执行；获得名额不自动提交任务。状态查询使用 `python3 "$coordinator_script" status`，不返回令牌。GUI 可单独申请 `--operation gui:submit-frontend --gui`，不要把短 GUI 控制权和长时间后台执行绑定在同一分配中。

## 中断、接管及迟到结果

短事务使用稳定文件锁和原子状态替换；逻辑分配不会因命令进程退出、Main 崩溃、心跳或时间经过自动消失。没有基于超时的清锁和强制释放选项。失联时停止冲突动作，核对原任务，取得明确交接或用户指定的接管授权；确认旧执行及副作用后才能用原令牌释放。令牌遗失或无法证明终止时保留现场并请求最小人工恢复，不删除协调目录绕过。

单调分配代次和随机令牌用于识别旧授权。旧结果必须进入所属 attempt 的隔离产物目录，Main 核对当前授权、输入哈希、基线和完整清单后再接受。旧令牌不能释放新分配；代次不是 OS 写入屏障，不能阻止绕过脚本的旧进程写源码。外部能力或恢复不可靠时，优先分配产物目录/隔离执行空间，由 Main 集成；直接共享写入必须保持独占直到确认停止。

生产、敏感访问、付费和不可逆操作仍核对各自授权。资源空闲不代表操作获准，两个项目分别获准操作也不代表能并发修改同一目标。现有服务冲突时不自动杀进程、改账号、重置数据库或删除卷。

## 验证边界

脚本测试使用临时 state 与临时项目，验证多进程竞争、容量、独占、部分申请回退、重复身份、退出后保留及异常状态。它们不证明 Gemini/Stitch/Antigravity 实际支持并行、取消、后台执行、目录隔离或业务 E2E。每个客户端仍按 operations.md、desktop.md 实测。纯文件/代码 REVIEW 不初始化本机协调状态或产品 `shared/`；若用户的只读审查需要 GUI 观察/切换共享桌面目标，仍须协调 GUI 控制权，但不因此获准修改产品。用户明确禁止任何文件写入时不初始化状态，改用已有证据或报告无法安全取得控制权。

## 统一资源身份

用同版本 [resource_identity.py](../scripts/resource_identity.py) 生成 JSON 中的 resource，作为 acquire 的 --resource 参数。所有参与项目共同遵守键协议，实际目标到非秘密标识的映射留在各项目记录中；仅声明键不证明实际占用已被发现或强制隔离。

| 类型 | 身份与保守策略 |
|---|---|
| port | host + protocol + port；本机别名 local/localhost/127.0.0.1/::1 统一，全部 bind 地址共用一个键，避免通配监听漏锁；远端别名不做 DNS 推断 |
| database | deployment + engine + database；postgresql/postgres、mariadb/mysql 归一，数据库名保留大小写；deployment 不能用 DSN/凭据，不同别名指向同一服务时先统一映射 |
| compose | daemon + 显式 Compose project name；产品根另作真实路径回执，不纳入排他键，因为不同源码目录相同 daemon/name 也会冲突；共享外部卷另设共同资源 |
| profile | 已存在浏览器 profile 的真实路径，符号链接别名统一；不因此获准读取其中私人内容 |
| client | app + instance；session 是回执元数据，**不同会话也不放宽本实例工程执行独占**。同会话当然串行；同项目按角色复用会话 |

```sh
python3 "$identity_script" port --port 3000 --protocol tcp --bind localhost
python3 "$identity_script" database --deployment dev --engine postgres --database app_test
python3 "$identity_script" compose --project-root "$product_root" --project-name app-dev
python3 "$identity_script" profile --path "$existing_profile"
python3 "$identity_script" client --app gemini-desktop --instance default --session "$session_id"
```

工具拒绝 URL、常见凭据格式和控制字符，但无法判断普通标签是否被人为填入秘密。它不读协调状态、不接触客户端；所有调用者必须使用同一协议和同一实际目标标识。旧版本已产生的 profile 哈希键无法从摘要反推出原路径；升级后先用各项目原记录核对别名，活动分配未协调前不混用新旧 profile 键。活动任务采用旧手写键时，先停止新派发、核对并释放原分配，再一致切换；不能仅生成新键就绕过旧锁。当前 exact-match exclusive 不能混用客户端粗/细粒度键；即使未来证明客户端可并行，也须先统一能力配置与资源重叠协议，再启用，不能任务私自降锁。不同项目仍可使用隔离的其他执行路线并行。

## 有限等待顺序

冲突的全资源请求返回 BUSY 与稳定 ticket、wait token，不持有任何部分资源。原 Main 保存回执；同身份、同 bundle 重试复用原位置，bundle 改变须先 cancel-wait。活动或等待中同 task 的另一 owner/attempt 属于防重复派发拒绝，不排队成另一份工作，先核对原执行。

等待上限 1000 项。对竞争同资源或开发容量的请求，较早且**当前资源可满足**的等待者优先；被其他资源阻塞的旧请求不冻结独立可执行工作。因此不是严格全局 FIFO，也不保证持续冲突下无饥饿。空闲后不会自动发放；Main 才可在合理检查点重试。已停止的 Main 留下的可满足旧请求可能阻止后来者，需原 Main/获准接管者取消，不能按年龄自动删除。

```sh
python3 "$coordinator_script" cancel-wait --token="$wait_token" \
  --confirmed --evidence 'Request cancelled before dispatch; no active grant released'
```

所有令牌参数使用 `--token="$token"` 等号形式，兼容以 `-` 开头的旧令牌；新令牌带稳定非选项前缀。等待令牌只取消等待，不释放运行分配；授权令牌只操作原分配。两者均不进入 public status 或提示词，分别保存在所属项目私有记录中。不因 BUSY 改 task/attempt/operation 制造新请求。短事务忙返回无队列回执，待事务可用后重试，不能据此派发。

## 容量变更、兼容与诊断

新状态采用本轮确认的 4/2/1 默认（整机开发/每项目开发/GUI），实际容量的唯一来源是本机共享配置。软件偏好唯一来源是调用项目规则；任务选择不写持久默认。已有状态迁移保留整机旧容量及所有授权，升级前后核对占用与配置；本轮只验证临时目录，不更改真实本机状态。

```sh
python3 "$coordinator_script" configure --development-limit 4 --confirmed \
  --evidence 'User authorized host development capacity four'
python3 "$coordinator_script" configure --project-root "$product_root" --project-limit 3 \
  --confirmed --evidence 'User authorized isolated project exception'
python3 "$coordinator_script" diagnose
```

configure 的 confirmed 是调用方已有授权的声明，不要求每次重新问用户，也不自动构成授权。工具允许 1..256，仅为输入上限，不代表机器承载能力；每项目例外保存在共同状态，不能通过 acquire 参数绕过。降低任一容量保留现有令牌和执行，不抢占；对应占用降到新上限以下才可再发。GUI 始终一个。

首次成功变更升级为 schema 3，schema 1/2 的活动授权、代次和令牌保留；只读查询不升级。schema 1 保留整机二，schema 2 保留其配置。旧版脚本拒绝 schema 3，回退前停止派发并核对活动与等待记录，不能覆盖回旧快照或让老 writer 继续管理。所有参与项目需实际读取新版工具，不能声称自动发现缓存已经更新。

状态保留最近 100 条 configure/acquire/release/wait/cancel_wait 事件，含非秘密 owner 身份、时间、代次及简短说明；release 关联原 grant 代次。队列重试/幂等读取/失败不逐条记录，裁剪前历史不保留。禁止源码、完整聊天、凭据、令牌进入事件；调用方 evidence 仍须脱敏。它只是有限操作轨迹，不是永久审计或独立恢复数据库。

diagnose 与 status 只读，不初始化目录，不判断进程存活；诊断中 liveness 明确 UNKNOWN_NOT_OBSERVED，并给出项目记录/实际客户端/副作用/原令牌检查项。Main 按上述逐资源条件确认整个 bundle 已不再使用、核对副作用后，才可用原 token release；交付子集关闭不证明后台执行停止。令牌遗失、执行未知或归属不明时请求最小用户决策，保留现场，不自动清锁、不杀进程。等待取消同样需原 wait token；未知时先询问。

macOS 路径身份通过内核 F_GETPATH 返回路径并核对设备/inode，统一 APFS firmlink 的可观察别名；其他系统按真实目录项归一化。既有目录被普通文件替换或祖先不可遍历时，不把原授权当作消失，保留其最近可观察祖先下的路径锁；仍允许诊断及核实后的原令牌释放。权限拒绝及身份变化异常不降级为正常目录。新申请要求真实目录。此处不是文件系统原子身份保证，路径后续变化仍需派发/集成前重新核对。
