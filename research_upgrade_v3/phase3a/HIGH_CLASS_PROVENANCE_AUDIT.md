# AquaVision High 类标签真实性审计

审计日期：2026-10-12  
结论：**High 是经过处理和重采样的 CyAN `CI_cyano` 数字值（DN）代理类别，不是现场实测危险等级，也不是毒素浓度或已经验证的 cells/mL 等级。**

## 证据链

本审计核对了 Zenodo 记录 `14230064` 的本地快照、固定上游代码 commit `e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37`、Phase 2–5 报告、v2 split、38,002 条已解码 reference census 和 288 条 v2 身份记录。Zenodo 快照 SHA-256 为 `0af19e8d9ee68c8e5e2ca9ba1f9e9be6b298502c775bfa08e0ee916c44c9afb6`，记录许可为 CC BY 4.0；deposit 的六个 ZIP 只提供 MD5。当前官方 CyAN 已发布 Version 6，但该事实不能反推 2019–2020 deposit 使用的确切处理版本。

支持的生成链如下：

1. NASA CyAN 日级 `CI_cyano` GeoTIFF 提供编码 DN，原始空间尺度约 300 m；DN 0 表示低于检测限，1–253 为数据，254 为 land，255 为 no-data/cloud 类标记。
2. 上游代码按 Sentinel-2 产品日期构造同一日 CyAN URL，把 Sentinel-2 和 CyAN 投影到 EPSG:4326，使用同一窗口裁剪。
3. CyAN 栅格被双线性重采样到由 warped Sentinel-2 决定的分辨率；这一步把粗分辨率代理信息插值到细网格，并不会创造独立的 20 m 生物观测。
4. Sentinel-2 导出的 cloud/land filter 进一步把 reference 写成 255；随后以 64×64、stride 64 切 patch。
5. 保存的 `*_sen2.npy` 是 12 通道 `uint16` 输入，`*_cyan.npy` 是 1 通道 `uint8` reference。最终 NPY 不含 CRS、仿射变换、footprint、lake ID 或 Sentinel 产品 UUID。
6. AquaVision 的像素映射是：DN 0–99→Low，100–199→Moderate，200–253→High；254、255 和无效值→ignore。High 因而只是最高的原生 DN 诊断区间。

## 逐项核验

| 要求 | 审计结果 | 证据强度 |
|---|---|---|
| 上游数据来源 | Sentinel-2 Level-2A 输入；NASA CyAN CI proxy reference；Zenodo `10.5281/zenodo.14230064` | 已核实到 deposit、代码和报告层 |
| 数据版本 | Zenodo record 固定；适用于各样本的 CyAN processing version 未保存 | 部分核实 |
| Sentinel 产品/scene ID | 上游代码曾把 `sen2_uuid` 传给保存函数，但未写入文件名或数组 | **UNVERIFIED** |
| 采集日期/时间 | 文件名保存日历日期；v2 为 2019–2020 数据 | 日期可核实；时刻 **UNVERIFIED** |
| CRS | 中间代码使用 EPSG:4326；最终数组没有 CRS/transform | 代码核实；逐样本 CRS **UNVERIFIED** |
| Footprint | 原始 window 和 raster transform 未随 NPY 保存 | **UNVERIFIED** |
| 空间匹配 | 同一窗口裁剪、CyAN 双线性重采样、数组索引切片 | 代码步骤已核实；历史实际配准精度未独立复测 |
| 时间匹配 | Sentinel beginposition 的日期与日级 CyAN URL 同日 | 日级匹配已核实；小时级误差/合成细节 **UNVERIFIED** |
| Low/Moderate/High | 0–99 / 100–199 / 200–253 | 已核实 |
| Ignore | 原 CyAN 254/255，加上 Sentinel-derived cloud/land masking；原因合并后不可分解 | 映射已核实；逐像素原因不可恢复 |
| High 的观测量 | 处理后 CyAN DN 最高 bin | 已核实为 proxy，不是物理危险等级 |
| 独立现场证据 | released dataset 不含与 patch 一一配对的现场细胞、chlorophyll、毒素或 advisory 标签 | 无 |
| 分辨率/重采样影响 | 约 300 m proxy 被重采样到约 20 m 网格，且在阈值前插值/量化 | 明确风险 |

## 科学可信性分层

- **可确认**：这些标签可以用于“用 Sentinel-2 预测该 released processed-CyAN reference bin”的复现实验。
- **统计关联**：模型性能说明 Sentinel-2 光谱与这一 proxy 有关联；不说明模型测得真实毒素、真实细胞数或现场危险。
- **需要进一步验证的假设**：High proxy 与具体湖泊中的生物量、毒性、健康风险或独立 bloom event 一致。
- **禁止表述**：不得把 High 自动称为“现场验证的高风险”“20 m 真实藻华标签”“毒素超标”或“部署级预警”。

## 可追溯样本输出

`GEOGRAPHIC_IDENTITY_TABLE.csv` 对全部 288 条 v2 样本逐条保存 split、网格 component、tile/subtile、日期、patch 索引、High/valid pixel 数和两类数组历史 SHA-256。缺失的 scene、lake、footprint、CRS、采集时刻和 bloom event 均写为 `UNVERIFIED`；没有从日期或文件名推测这些身份。

主要来源：

- [Zenodo dataset record](https://doi.org/10.5281/zenodo.14230064)
- [固定的上游数据处理代码](https://github.com/cschloer/hab_detection_s2/tree/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37)
- [NASA CyAN Version 6 release notes](https://oceancolor.gsfc.nasa.gov/images/cyan/version/6/CyAN_NASA_MERISOLCI_CI_release_notes_V6_Feb_2025.pdf)
- [EPA CyAN project](https://www.epa.gov/water-research/cyanobacteria-assessment-network-cyan)

## 判定

标签来源在“deposit + 保存代码 + DN 映射”层面可追溯，但逐样本原始产品和地理身份没有完整保存。研究证据等级是 **processed remote-sensing proxy with incomplete scene/geospatial provenance**。这足以支持受限的 proxy-reproduction 研究，不足以支持真实环境危险分类或外部地理泛化结论。

