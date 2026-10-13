# AquaVision 新独立 High 样本可行性审计

审计日期：2026-10-12  
结论：**公开数据源具备构建新数据的技术可行性，但本轮没有找到可立即声明为独立、与旧数据不重叠且已完成身份核验的 High 样本集。**

## 候选来源

### 1. 现有 Zenodo deposit

[Zenodo record 14230064](https://doi.org/10.5281/zenodo.14230064) 的本地 catalog snapshot 记录 CC BY 4.0，六个 archive 约 23.4 GB。38,002 个已解码 reference 中有 12 个含 High author-grid component，7 个通过旧操作性 support gate；完整索引有 404,450 对、38 个 connected components，但 366,448 个 reference 未解码。

这些未使用 component 可用于**探索性扩充**，但 deposit 不保存真实 lake、scene UUID、CRS/footprint 或 bloom-event ID。仅从同一 deposit 增加 patch/日期不能满足 v3 的 verified geographic independence，且已筛选 support 的 38,002 个 reference 不能称为盲新样本。

### 2. NASA CyAN + Copernicus Sentinel-2 重新构建

NASA 当前公开 CyAN Version 6 的 CI product；[Version 6 release notes](https://oceancolor.gsfc.nasa.gov/images/cyan/version/6/CyAN_NASA_MERISOLCI_CI_release_notes_V6_Feb_2025.pdf) 明确其为 satellite-derived CI 产品。[EPA CyAN](https://www.epa.gov/water-research/cyanobacteria-assessment-network-cyan) 说明数据可公开获得，但这仍是 satellite proxy。2025 Version 6 与旧 deposit 未知 processing version 不可直接混为同一 target version。

[Copernicus Data Space](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2) 提供 Sentinel-2 L1C/L2A 历史和当前产品；[官方条款](https://dataspace.copernicus.eu/terms-and-conditions) 说明 Sentinel data 按 free, full and open basis 提供，并要求适当署名。其 catalog/API 可保存 product ID、sensing time、tile、processing baseline 和 footprint，能够修复旧 deposit 的关键身份缺口。

这一路径技术上可行，但需要新 ETL、版本锁定、空间重投影误差分析和预先冻结匹配规则；不能把 Version 6 新标签与旧标签直接混合而不做 domain/version study。

### 3. 水体身份和现场证据

[USGS NHD/NHDPlus HR](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) 提供水体 polygon/永久标识；[USGS identifier crosswalk](https://www.usgs.gov/data/crosswalk-waterbody-identifiers-between-national-hydrography-dataset-plus-high-resolution) 是 CC0，可关联 NHDPlusHR、NHDPlusV2 和 HydroLAKES ID。水体 polygon 可以把同一湖泊的 patch 强制归为同组。

[EPA Water Quality Portal](https://www.epa.gov/waterdata/water-quality-data-download) 提供来自联邦、州、部落等来源的现场水质记录；[EPA HAB data](https://www.epa.gov/habs/hab-data) 说明其中包括藻类组成和 toxin 数据。它适合建立外部现场验证子研究，但采样深度、实验方法、时区、检测限和卫星过境时间必须逐条核对。现场 toxin 与 CyAN High 是不同 estimand，不能直接当作原三分类标签替换。

## 预先固定的采样设计

若启动数据构建，应在查看任何模型预测前：

1. 固定数据版本：CyAN product version、Sentinel-2 collection/processing baseline、NHD release、WQP export timestamp 与查询参数。
2. 固定时间规则：只保留 Sentinel sensing time 与 CyAN acquisition/composite window 可解释匹配的 pair；现场样本另设例如 ±24 h 主分析和 ±72 h sensitivity analysis，不事后调整。
3. 固定空间规则：保存原始 CRS、footprint；使用水体 polygon 裁剪，任何 footprint 相交或同一 waterbody 的样本进入同一 group。
4. 去重：以 `(Sentinel product ID, CyAN granule ID, waterbody permanent ID, footprint)` 为 observation identity；同 scene 多 patch 不增加独立 scene 数。
5. 候选抽样只依据 geography/date/source label support 和质量条件，不读取旧/新模型 prediction。
6. 先分组再切分：按完整 waterbody 和 scene/event cluster 分配；目标至少 3 个 verified High units/partition，并尽量提高到 ≥10 个 Validation units 后再估计 cluster bootstrap CI。
7. 新 Test 在下载/标注后立即 seal；只有 Train/Validation 可用于 Phase 3B。
8. 与旧 v2 做 footprint、waterbody、scene/product 和 date overlap 检查。由于旧 v2 footprint/scene 缺失，必须先向作者或从原始生成 metadata 恢复旧身份；否则“与旧数据不重叠”无法被完全证明。

## 可行性判定

- **数据访问/许可**：总体可行；Zenodo、Copernicus、NASA/EPA、USGS/WQP 都有公开入口，但各数据集应单独保留许可和署名记录。
- **立即获得合格独立 High 单元**：尚未完成。当前只有候选来源，未生成 sealed manifest，未验证数量。
- **最小补救**：先恢复/重建带 product ID、timestamp、CRS、footprint 和 waterbody ID 的 metadata-only catalog；完成 overlap 与 High support census；达到 v3 数据门槛后再允许训练。
- **不能采用的捷径**：从同一 scene 切更多 patch、按模型预测筛数据、把不同 CyAN 版本直接混合、把 WQP toxin 样本直接改名为 CyAN High。

