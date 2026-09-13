# Week 3 字段与生命周期对照

状态：Jack 已于 2026-09-13 批准本对照表；不代表完整规格获批，不包含代码实现。

对照来源：[数据模型](../02-data-model.md)、[业务规则与固定流程](../03-domain-invariants-pipeline.md)、[周计划与验收](../08-milestones-acceptance-criteria.md)，以及当前 schema、数据库和确认接口。

## 1. 范围与当前事实

- Week 1–2 按已约定的精简范围完成，不重新打开。
- 当前 FactDraft 包含 claim、evidence_quote、source_sequence。抽取后只返回草稿并保存 Run；确认接口才插入 facts。
- facts 和 source_spans 已有数据库 ID，但现有返回类型不暴露这些 ID。
- Document、SourceSpan 已能一起事务保存；抽取和确认读取持久化片段。
- Week 3 开始持久化待审核候选，并按 ID 更新审核状态。这是明确的接口行为变化，不能只增加 status 字段后仍然在确认时插入新记录。
- 本文提出后续字段的落地顺序；未获确认的简化不自动覆盖正文的 Required fields。

## 2. 术语对应

| 名称 | 含义与当前对应 |
|---|---|
| ModelFactOutput | 模型提出的声明与引用；不含用户审核状态 |
| FactDraft | 沿用并扩展现有类，承载待审核事实及审核信息；本周不另起一套同义模型 |
| Fact | 数据库中可被审核的事实记录；pending / confirmed / rejected 表示状态，不表示三种不同实体 |
| claim（当前字段） | 对应规格 Fact.summary，本周保留名称；不是 Week 5 生成建议里的 Claim 实体 |
| SourceSpan | 固定保存的原文片段；声明编辑不得改写它 |
| FactEvidence | 规格中的事实与原文关联；当前以 document_id + source_sequence + evidence_quote 直接表达单来源关联 |
| Run | 当前是单次抽取的执行记录，成功不代表用户确认 |

## 3. Week 3 拟实现字段

### FactDraft 与 facts

| 字段 | 当前情况 | Week 3 方案与用途 |
|---|---|---|
| id | 表中已有，返回类型没有 | 保存候选后返回稳定 ID；确认、编辑、拒绝针对这个 ID |
| claim | 已有 | 当前可编辑声明；暂不改名为 summary |
| original_claim | 无 | 新候选创建时保存原始声明，以后编辑不得覆盖 |
| evidence_quote | 已有 | 固定保存原始引用，本周声明编辑不修改引用或来源 |
| document_id | 当前由请求单独携带，表中已有 | 返回的持久化候选能够识别所属文档；不接受编辑改来源 |
| source_sequence | 已有 | 保留当前关联方式，本周不重做来源模型 |
| status | 无 | pending / confirmed / rejected；新候选默认 pending，由服务处理操作后更新 |
| extraction_run_id | 无 | 新候选关联实际成功抽取 Run；旧记录允许缺失，不虚构历史关联 |
| created_at | 表中已有 | 返回审核记录需要的创建时间 |
| updated_at | 无 | 状态或声明修改时更新 |
| confirmed_at | 无 | 用户确认时记录；失去 confirmed 状态时清空当前确认时间 |

扩展 FactDraft 不等于让模型生成上述全部字段。模型仍只输出声明与引用；ID、状态、来源、时间和 Run 关联由程序负责。未保存的对象尚无 ID，保存后必须有 ID；接口返回值需明确这一点。

本周保留“原始声明 + 当前声明”，不建设完整多版本编辑历史。是否需要更多历史事件留待真实需求出现，不隐含承诺。

### Job 与 JobRequirement

| 模型 / 字段 | Week 3 方案 |
|---|---|
| Job.id、source_text | 程序生成稳定 ID，保存原始职位描述 |
| Job.source_hash、language、imported_at、extraction_version | 随职位输入保存；语言允许未知，版本来自配置；hash 不代表本周增加重复导入处理 |
| JobRequirement.id、job_id | 程序分配并保存；读取同一条记录时稳定，不要求多次模型抽取产生相同 ID |
| requirement_text | 保留职位描述中支持该要求的原文，并校验确实存在 |
| normalized_requirement | 模型规范化的要求描述 |
| category | 使用小而明确的分类，不引入复杂分类体系 |
| required_or_preferred | 必需 / 优先；建议允许 unspecified，避免原文不明确时强行猜测，需同步正文定义 |
| years_or_level | 只记录原文明示的年限或等级，没有则为空 |
| priority、status | 已决定延后，直到存在明确的消费行为再定义 |

职位抽取需要沿用模型、prompt、结果和错误的运行记录能力。当前 ModelFactRun 强依赖 document_id 和 source_sequence，不能塞入假的履历来源来记录职位调用；开始职位抽取前，应先明确 Run 如何表达两种输入来源。这是 Week 3 的依赖设计，不是整套 RunStep / RunEvent 平台。

## 4. 审核生命周期（建议采用的明确语义）

| 操作 | 前置状态 | 结果 | 保留与检查 |
|---|---|---|---|
| 抽取成功、引用有效 | 尚无候选 | 保存 pending 候选并返回 ID | 固定原始声明、引用、来源和成功 Run 关联 |
| 抽取或引用校验失败 | 尚无候选 | 保存失败 Run，抛出错误，不创建候选 | 保留失败原因 |
| 确认 | pending | 同一条记录变 confirmed | 重新检查持久化来源与引用，记录确认时间 |
| 编辑声明 | pending / confirmed / rejected | 更新 claim，状态回 pending | original_claim、引用和来源不变；清空当前 confirmed_at |
| 拒绝 | pending / confirmed | 同一条记录变 rejected | 保留原始数据，清空当前 confirmed_at，不物理删除 |
| 重复确认 / 重复拒绝 | 已处于目标状态 | 返回当前记录，不重复插入 | 不因重复确认改写首次进入当前确认状态的时间 |
| 直接确认 rejected | rejected | 拒绝此转换 | 本周可先编辑回 pending 再确认，不另做恢复接口 |
| 后续检索与生成 | 任意 | 只接受 confirmed | 客户端传 status=confirmed 不能绕过确认操作 |

编辑后重新审核，是防止“曾经确认过的声明被改成另一句话，却仍有确认资格”。此转换属于本草案建议，确认后再作为实现依据。

## 5. 迁移和 API 边界

- 当前确认接口接收整份草稿并插入 Fact；新审核流程应接收候选 ID，对已有记录操作。提前确定请求与响应变化，再写 TDD 测试，避免并行维护两套审核流程。
- 沿用现有 FactDraft 作为记录模型，不代表确认、编辑请求必须开放全部字段。请求只接收该操作允许改变的内容。
- 旧 facts 都由确认路径保存，可迁移为 confirmed；用已有 claim 初始化 original_claim。
- 旧 Run 与 Fact 没有可靠直接关联，不猜测 extraction_run_id；旧确认时间不明时保持缺失，不把 created_at 冒充 confirmed_at。
- 迁移负责保留旧记录与 ID，不要求删除真实数据库重建。
- Week 3 保留确认、编辑、拒绝 UI。界面串起导入 → 查看来源片段 → 抽取候选 → 审核，用户无需在三个独立 API 之间手动搬运 ID 和草稿；显示操作结果、错误和审核状态。

## 6. 后续字段及依赖

| 内容 | 安排 | 本周边界 |
|---|---|---|
| Document.document_type、parser_name、parser_version、status | 后续来源元数据整理，具体周次待排 | 不作为重开 Week 2 的条件 |
| Document.content_hash、SourceSpan.body_hash | Week 4 建索引前对齐 | 不附带重复导入检测 |
| original_filename / imported_at | 与当前 filename / created_at 对照 | 不因命名不同立即改表 |
| SourceSpan.id、location_type、location_data | Week 4 证据标识对齐 | 标题片段已是当前支持粒度，不恢复表格解析 |
| FactEvidence 多对多、support_type | Week 4 检索前明确，Week 5 引用依赖它 | 暂保留当前单来源关联；没有决定永久取消多对多 |
| Fact.fact_type、organization、project、dates、skills、attributes | Week 4 依据检索输入确定需要的子集，其余延后 | 不在审核流程里一次实现八种细分类型 |
| conflicting / 冲突证据 | Week 5–6 生成与评估前明确 | 不是直接塞进三状态审核流程；冲突不能自动成为可发布声明 |
| RetrievalCandidate、候选分数、排名、selected | Week 4 | 尚未实现是按计划推进 |
| Suggestion、Claim、ClaimEvidence | Week 5 | 保留每条生成声明的证据关联 |
| Run 检索配置、tokens、latency、cost、版本与 hash | 对应阶段记录，Week 7 汇总 | Week 3 只解决职位调用与事实调用共用记录的来源表达 |
| RunStep / RunEvent、Agent 工具事件 | Week 7–8 | 不提前建设通用事件框架 |

## 7. 已决定的范围调整

### 已决定

- v1 不支持 DOCX、TXT、LinkedIn CSV 导入，保持 Markdown 等当前支持输入。
- Week 2 不做表格单元格级解析、重复导入检测；不追加模拟解析器变化的专项测试。
- Week 10 不要求固定公开或私有案例数量。
- 其他周暂时保留，进度明显落后时再讨论调整。

以上决定不等于删除 FactEvidence、Agent、judge 或所有 hash 字段。

### 本次已确认

| 项目 | 决定 | 理由 |
|---|---|---|
| extraction_confidence | 从 v1 必需字段移除 | 模型自报置信度没有校准依据，当前也没有明确用途；绝不能替代确认状态 |
| JobRequirement.priority、status | 延后至有明确用途 | 避免制造没有消费者的状态和排序字段 |
| 确认、编辑、拒绝 UI | 保留在 Week 3，串联导入、抽取和审核 | 三个独立 API 操作分散，需要界面提供连贯使用流程 |

## 8. 开发顺序与固定检查点

先确认本文的生命周期和范围，再逐条 TDD；不一次写全部测试或全部实现。

1. 候选持久化：新候选为 pending，获得稳定 ID、原始声明与来源、Run 关联。
2. 审核：确认、拒绝更新同一记录；编辑保留原始值且退回 pending；未确认记录不可进入可用事实集合。
3. 迁移：旧确认事实和 ID 保留，不虚构缺失历史信息。
4. 职位抽取：原文保存、结构化要求、必需/优先/未说明、明示年限、运行记录与失败路径。
5. 完成连贯的导入、抽取、审核 UI，显示证据与状态并处理失败；具体布局在实现前确定。
6. 用固定的小组职位样例人工比较实际模型输出；单元测试不替代语义效果评估。

测试数量不在本文提前扩大；每一项开始前给出有限的行为清单与观察方法。Week 3 的 API、身份与字段语义在开始前一次对齐，避免边写边改名、重复替换保存路径。
