# AquaVision Prospective v3 Dataset 防污染协议

冻结日期：2026-10-12  
状态：**设计就绪；数据尚未达到资格门槛。**

## 1. 研究对象

Prospective v3 预测一个预先冻结版本的 processed CyAN `CI_cyano` proxy bin。它不以现场危险、毒素或细胞数为标签。旧 v2 Validation/Test 和本轮已查看 High support 的 12 个 author-grid components 全部是 legacy evidence，禁止重新包装为独立 confirmation set。

## 2. 两阶段数据构建

### Stage 1：metadata-only candidate catalog

在下载影像前保存：

- permanent waterbody ID、版本化 polygon 和所有别名；
- Sentinel product ID、sensing timestamp、MGRS、processing baseline、CRS、footprint；
- CyAN product ID、processing version、composite period、checksum、CRS/transform；
- frozen spatial/temporal matchup rule、license 和拒绝原因；
- 与所有 legacy footprints/waterbodies/scenes/dates 的 overlap 状态。

任何缺项保持 `CANDIDATE` 或 `UNVERIFIED`，不得进入正式 split。

### Stage 2：support census

只有 Stage 1 identity gate 通过后才下载必要的 label windows。High support screening 可以使用 source labels，但必须在模型预测之前完成；所有候选和拒绝项均保留。不得按旧模型或新模型 prediction 挑样本。

## 3. 独立单位与污染图

基本 unit 定义为 `waterbody permanent ID × non-overlapping scene/event cluster`。以下任一关系存在时必须合并为同一 connected group：

1. 同一 waterbody polygon；
2. Sentinel product 相同或 footprints 相交；
3. patch footprints 相交或距离小于预注册 buffer；
4. 同 waterbody 且日期差不超过冻结 event window；
5. 同一 CyAN source granule 的重叠/相邻 interpolation support。

默认建议 event window 为 30 天，但必须在首次 support census 前依据生态目标固定；不得为了增加 unit 数事后缩短。

## 4. 数据用途

| Partition | 用途 | 最低 High units | 访问规则 |
|---|---|---:|---|
| Train | fitting 和 fold-internal preprocessing | ≥3 | 可反复用于训练 |
| Validation | 资格和模型选择 | ≥3，覆盖≥2 waterbodies、≥3 scenes；目标≥10 | 可按冻结协议使用 |
| Confirmation | 一次性外部确认 | ≥3，目标≥10，且与开发数据完全断开 | 模型与分析锁定后开启一次 |

每个含 High unit 的旧最低 support 仍为 ≥2 dates、date span ≥30 days、≥3 High patches、≥100 High pixels。它只是可计算门槛，不是统计充分性保证。

## 5. 分配顺序

1. 在模型代码运行前冻结全部合格 units 和 contamination graph。
2. 先抽取 confirmation groups 并 seal manifest、hash 和访问日志。
3. 剩余 groups 再分 Train/Validation；相同 connected component 不可拆分。
4. 三类必须在 Train 和 aggregate Validation 中可计算。
5. 所有 scaling、normalization、sampling、augmentation、class weights 和 calibration 只能在相应训练折拟合。

## 6. 模型与评价防污染

- 延续 `EXPLORATORY_V3_SELECTION_PROTOCOL.md` 的 High Recall/F1、Low/Moderate、Macro-F1、equal-component 指标和 `NO QUALIFIED MODEL`。
- legacy v2 只能用于背景描述，禁止选择 architecture、loss、weight、threshold 或 stopping point。
- Confirmation 只在唯一模型、代码 commit、环境、primary analysis 和 failure rules 锁定后运行一次。
- 查看 confirmation 后的任何调整必须创建新的 future confirmation set；原结果永久保留为失败/已查看证据。

## 7. 当前候选状态

`INDEPENDENT_HIGH_CANDIDATES.csv` 登记 12 个旧 deposit High-bearing author-grid candidates，其中 6 个已进入 v2，6 个未进入 v2但其标签 support 已被 screening 查看。由于 waterbody、scene、footprint 和 CyAN version 均未核实，**0 个**可用于 prospective Validation，**0 个**可用于 Confirmation。

## 8. 停止条件

- 无法唯一确认 product/footprint/waterbody；
- 当前处理版本无法与冻结 target 一致；
- overlap graph 使 High units 少于最低门槛；
- label support 依赖重复裁剪而非独立 units；
- 需要根据模型预测修改候选或 split；
- Confirmation 被提前查看或访问日志异常。

触发任一项时输出 `DATA GATE FAILED`；不得通过更复杂模型弥补证据缺口。
