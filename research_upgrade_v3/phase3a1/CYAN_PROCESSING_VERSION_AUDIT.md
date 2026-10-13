# CyAN 处理版本与标签解释审计

审计日期：2026-10-12  
版本判定：**UNVERIFIED**

## 可以确认的产品链

上游代码构造的产品名称为：

`LYYYYDDD.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m_<tile>.tif`

冻结样本保留 2019–2020 日历日期及 tile ID，且 288/288 processed CyAN arrays 已与 Zenodo 原件逐哈希匹配。代码证明 intended chain 为日级 `CI_cyano` → EPSG:4326 warp → 与 warped Sentinel resolution 对齐的 bilinear resampling → 相同 window crop → Sentinel-derived cloud/land mask → 64×64 array slice。

这些证据确认处理逻辑和最终 bytes，不确认生成时使用的 NASA processing version、原始 GeoTIFF checksum 或实际 GDAL version。

## 为什么不能认定为 Version 5

[NASA Version 5 release notes](https://oceancolor.gsfc.nasa.gov/images/cyan/version/5/CyAN_NASA_MERISOLCI_CI_release_notes_V5_6May_2023.pdf) 记录 V5 于 2023 年 5 月发布；Zenodo deposit 于 2024 年发布，因此 V5 在时间上是一个候选。但代码和 arrays 没有 version tag，数据可能在此前生成或由后续 reprocessing 替换。当前 [Version 6 release notes](https://oceancolor.gsfc.nasa.gov/images/cyan/version/6/CyAN_NASA_MERISOLCI_CI_release_notes_V6_Feb_2025.pdf) 明确 V6 于 2025 年发布，不能把当前下载内容倒推为历史版本。

结论必须保持：V5 **plausible candidate, not confirmed**；V6 不适用于解释冻结 bytes，除非未来通过原始 checksum/reprocessing ledger 证明。

## DN、flags 与 mask

- 原生语义：0 为 below detection；1–253 为 CI data；254 为 land；255 为 no-data/cloud 类标记。
- 历史代码尝试在 warp 中把 254 映射为 255，并用 Sentinel-derived land/cloud filter 写入更多 255。
- 最终数组无法区分 255 究竟来自原产品 no-data、cloud、land remapping 还是额外 Sentinel mask。
- 288 个冻结 arrays 共 1,179,648 pixels：840,810 个 `<254`，338,838 个 255，0 个 254。

## 双线性重采样与类别边界

CyAN 约 300 m proxy 被 bilinear resampling 到 warped Sentinel 网格，然后保存为 `uint8`，最后才按 0–99、100–199、200–253 分箱。双线性插值可以产生原始邻近 pixels 中不存在的中间 DN；历史代码没有保存 pre-resample values 或 rounding ledger，因此无法对每个像素判断它是否为原始观测或插值结果。

冻结 v2 arrays 在阈值附近包含：DN 99 为 1,309 pixels、100 为 1,087、199 为 1,935、200 为 1,912。它们说明分箱对插值/量化边界敏感，但不能证明这些具体 pixels 都由插值产生。

## 科学解释

High 始终定义为**处理后的 CyAN DN 200–253 proxy bin**。它不是现场毒素、细胞数、公共健康 advisory 或独立 bloom event。原始标签和历史阈值全部保留，本轮未重新标注，也未根据模型表现调整边界。

## 最小补救

要确认版本，至少需要生成时 CyAN GeoTIFF 的 checksum/header、NASA processing metadata 或作者 download ledger。当前 NASA file download 需要 Earthdata authentication；本轮没有绕过权限，也没有把当前重处理产品当作历史原件。
