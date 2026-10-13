# AquaVision 物理空间重叠审计

审计日期：2026-10-12  
结论：**未确认任何跨 split 的实际 footprint 重叠，但由于 288/288 footprints 均未恢复，也不能确认不存在重叠。**

## 几何精度与证据强度

| 检查 | 精度/单位 | 结果 | 证据强度 |
|---|---|---|---|
| sample ID overlap | 完整 frozen ID | 0 | CONFIRMED |
| author component overlap | 同 CyAN tile 的 selected-parent adjacency | 0 | CONFIRMED，但不是物理几何 |
| source parent overlap | filename parent ID | 0 | CONFIRMED grid identity |
| Sentinel array hash overlap | exact bytes | 0 | CONFIRMED content identity |
| filename patch-position overlap | parent + relative row/column | 0 | CANDIDATE physical identity |
| actual footprint intersection | CRS geometry | 不可计算 | UNVERIFIED |
| same waterbody across split | permanent waterbody identity | 不可计算 | UNVERIFIED |
| same Sentinel product across split | product UUID/ID | 不可计算 | UNVERIFIED |
| same bloom event | event evidence | 不可计算 | UNVERIFIED |

不同 array hash 只证明字节不同，不证明地理位置不同。author components 只是在不完整 selected-parent graph 中隔离；同一湖泊可能跨越 component、未选择的中间 parent 或 CyAN tile 边界。

## 时间与重复采样

- Train/Validation/Test 分别有 50/29/75 个 parent-date candidate groups。
- 三个 split 内重复的 parent-relative patch positions 分别为 11、14、17 个位置，对应额外重复记录 13、18、27 条。
- Train–Validation、Train–Test、Validation–Test 分别共享 13、6、5 个日历日期。
- 同一 parent/date 内的多个 patch 来自同一处理批次候选，不能计作独立 scenes。
- 相同 parent-relative position 跨日期是候选重复 footprint；没有 affine/CRS 时不能计算真实位移或把 30 天阈值解释为独立 bloom event。

## CyAN 内容重复

三个 split 两两共享 SHA-256 `06a9c033…eeeed`，对应全 Low processed reference 内容。该重复可能由不同地点的同质全 Low mask 产生，不足以证明物理重复；但它说明不同 sample ID 不等于独立标签信息。

## 保守 group identity

后续 prospective 数据必须把以下关系构成一个不可拆分的 connected group：

1. 同一永久 waterbody；
2. 相同或相交 Sentinel product footprint；
3. patch footprint 相交或接触预先规定 buffer；
4. 同一 scene/acquisition；
5. 同一 waterbody 内处于冻结 temporal event window 的观测。

当前历史样本缺少前三项所需几何，因此不能生成可信 group identity。自动化函数在缺少 waterbody、scene 或 footprint 任一项时 fail closed。

## 判定

现有 v2 仍只能称为 **author-grid-component separated legacy benchmark**。没有证据支持“跨湖泊”“跨 scene”或“物理不重叠”结论。
