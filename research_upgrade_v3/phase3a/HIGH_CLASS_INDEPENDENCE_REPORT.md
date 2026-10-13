# AquaVision High 类独立性审计

审计日期：2026-10-12  
结论：**现有 v2 split 在作者网格 component、subtile、sample ID 和 Sentinel 数组哈希层面隔离；但湖泊、真实场景、物理 footprint 和 bloom-event 独立性均无法确认。**

## 计数单位

像素、patch、日期、subtile、作者网格连通分量、湖泊、卫星 scene 和 bloom event 是不同的依赖单位。37,768 个 Test High 像素不是 37,768 个独立验证样本；它们来自 28 个含 High patch、3 个作者网格 component，并且这些 component 是否对应独立湖泊/scene/event 仍为 `UNVERIFIED`。

| Split | patch | 含 High patch | High pixel | 作者网格 component | 已确认独立 lake | 已确认独立 scene | 已确认独立 bloom event |
|---|---:|---:|---:|---:|---|---|---|
| Train | 96 | 6 | 647 | 2 | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| Validation | 48 | 4 | 931 | 1 | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| Test | 144 | 28 | 37,768 | 3 | UNVERIFIED | UNVERIFIED | UNVERIFIED |

`component` 是根据完整已索引作者 50-pixel parent grid 的对角相邻关系建立的最小共址约束，不是湖泊 ID。不能把上表中的 2/1/3 当作已证明的 2/1/3 个湖泊或场景。

## High 支持集中度

| Split / component | High pixel | Split 内占比 | 含 High patch |
|---|---:|---:|---:|
| Train / `6_5_X0250_Y0300` | 364 | 56.26% | 3 |
| Train / `7_5_X1300_Y0900` | 283 | 43.74% | 3 |
| Validation / `6_5_X0250_Y0450` | 931 | 100% | 4 |
| Test / `6_2_X0500_Y1150` | 6,345 | 16.80% | 6 |
| Test / `6_2_X0650_Y0900` | 3,573 | 9.46% | 3 |
| Test / `7_5_X1800_Y1700` | 27,850 | **73.74%** | 19 |

Validation 的 High 模型选择实际只由 1 个 candidate component 支撑。Test pooled High 指标则主要由一个 component 决定，因此像素池化指标会明显高估地理复制量。

## 跨 split 检查

自动检查结果保存在 `SPLIT_OVERLAP_AUDIT.csv`：

- sample ID：三组两两重叠均为 0。
- author-grid component：两两重叠均为 0。
- source subtile：两两重叠均为 0。
- filename patch-position candidate：两两重叠均为 0。
- Sentinel-2 数组 SHA-256：两两重叠均为 0。
- acquisition date：Train–Validation 13 个、Train–Test 6 个、Validation–Test 5 个日期重合。日期重合本身不是泄漏，但在 scene ID 缺失时不能排除同一轨道/场景关系。
- CyAN reference SHA-256：每一对 split 均共享同一哈希 `06a9c0…eeeed`。该内容对应全 4096 像素均落在 Low 的相同 reference 数组，并在多个不同日期/位置重复出现。它是**标签内容重复**，不是已证明的同一物理 patch；不能据此断言地理泄漏，也不能忽略由大量同质 label 带来的有效信息重复。
- lake、scene、footprint、真实物理 overlap、bloom event：全部 `UNVERIFIED`，不能计算 overlap 数量。

## 时空近重复与相关性

在 v2 含 High patch 内：

- Train：6 个 High patch、6 个位置；2 个 patch 存在同日相邻 High patch。
- Validation：4 个 High patch、3 个位置；1 个位置跨日期重复，2 个 patch 存在同日相邻 High patch。
- Test：28 个 High patch、21 个位置；4 个位置跨日期重复，其中 3 个在 30 天内重复；6 个 patch 存在同日相邻 High patch。

更大范围的 38,002-reference screening 也记录了同日相邻、跨日期重复位置与近时重复。它们说明 patch 不是独立抽样单位。30 天间隔只是操作性过滤，不证明是新的生物事件。

## 已确认与未确认

**Confirmed finding**

- v2 的 sample/component/subtile/Sentinel-array hash 没有跨 split 重叠。
- Validation 只有 1 个 High component、4 个 High patch；Test 一个 component 占 73.74% High pixels。
- 存在重复位置、相邻 patch 和相同 reference 内容。

**Statistical association / descriptive evidence**

- 历史模型 High 性能随三个 Test component 明显变化；只有三个 candidate units，不能估计可靠总体区间。

**Unresolved**

- 独立湖泊数、独立 scene 数、footprint overlap、跨 tile 物理邻接、独立 bloom-event 数。

**Requires external verification**

- 任何“跨湖泊泛化”“跨 scene 泛化”或“跨独立藻华事件泛化”结论。

## 判定

现有 split 通过了**命名网格层面的完整性检查**，但没有达到研究目标所需的真实地理独立性证明。Validation 的一个 High component 不足以可靠选择针对 High 的模型。当前有效结论必须限制为 legacy v2 candidate-component benchmark。

