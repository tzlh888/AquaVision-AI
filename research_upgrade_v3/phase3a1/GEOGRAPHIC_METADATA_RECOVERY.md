# AquaVision 历史地理元数据恢复

审计日期：2026-10-12  
判定：**Historical geographic identity recovery — NOT READY**

## 结果摘要

针对冻结 v2 的 288 个样本，已确认日期、CyAN tile、作者 parent grid、相对 64×64 数组窗口、split、两类数组 SHA-256；但没有任何样本恢复到可核验的真实 patch footprint、Sentinel product/scene、MGRS tile 或 waterbody identity。

| 字段 | CONFIRMED | CANDIDATE | UNVERIFIED |
|---|---:|---:|---:|
| 日期（天） | 288 | 0 | 0 |
| 相对 array crop offsets | 288 | 0 | 0 |
| 原始 Sentinel arrays | 288 | 0 | 0 |
| Sentinel product/scene ID | 0 | 0 | 288 |
| acquisition timestamp | 0 | 0 | 288 |
| MGRS tile | 0 | 0 | 288 |
| source CRS/affine/crop window | 0 | 0 | 288 |
| actual patch footprint | 0 | 0 | 288 |
| waterbody ID/geometry | 0 | 0 | 288 |
| CyAN filename pattern | 0 | 288 | 0 |
| CyAN processing version | 0 | 0 | 288 |

逐样本结果见 `PATCH_IDENTITY_CATALOG.csv`。空值是证据缺失，不代表“不存在”。

## 为什么 Sentinel array 不能恢复 scene identity

固定上游代码将 `sen2_uuid` 传入 `save_data`，但 `save_data` 不把 UUID 写入 filename、NPY header 或 sidecar。文件名只保留 parent ID、日历日期及数组偏移。`create_dataset.py` 又以 `(parent, date)` prefix 防止重复写入，因此同一 parent/date 的 patches 可以作为**相关处理批次候选组**，却不能反推出被首先保存的产品 UUID。

原始 `data.json` 应包含每个 parent 的 EPSG:4326 crop window，但它不在 Git tree、历史 ZIP、Zenodo archive 或当前缓存中。CyAN tile 及 X/Y/S 是源栅格索引，不是经纬度，也不是 MGRS。

## Copernicus STAC 核验

已对官方 [Copernicus Data Space STAC](https://stac.dataspace.copernicus.eu/v1/) 执行 metadata-only probe：

- `sentinel-2-l2a` collection：HTTP 200，响应 SHA-256 `ed49673e…c0685a`。
- collection queryables：HTTP 200，响应 SHA-256 `2a9d10d6…20dc7`。
- 仅以 2019-03-17 日期、无 geometry 的 control search：HTTP 200，但首项位于 MGRS `57KUR`、澳大利亚。它与 AquaVision 样本没有匹配意义，只证明 date-only 查询不具识别性。

官方 STAC 支持 product ID、datetime、geometry、MGRS/grid 等检索，但当前缺少历史 window/footprint，不能构造样本级空间查询。即使未来只得到一个当前 STAC candidate，也仍需确认它与旧 SciHub UUID及历史处理 baseline 相同；当前目录可能包含后续 reprocessing 的产品，不能自动升级为 `CONFIRMED`。

## CyAN 和水体位置恢复尝试

NASA Ocean Color direct-access 目录能确认历史日级产品文件名存在，但实际 GeoTIFF 下载重定向到 Earthdata authentication。本轮没有凭证，未绕过访问控制。没有原始 GeoTIFF header，就不能重建 2000×2000 tile 的精确 transform 和 parent window。

[USGS National Hydrography](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) 可以在 footprint 已知后提供永久水体 identity 和 geometry；当前没有可查询的可靠 footprint，因此没有执行坐标猜测，也没有从作者图像或 component 名编造 lake ID。

## 已恢复的有限结构

- Train/Validation/Test 分别有 50/29/75 个 `(author parent, date)` candidate processing-run groups。
- 同一 parent/date 下的 patches 很可能共享一次 `download_and_process` 调用，因而不能作为独立 scenes。
- 不同 parent/date 仍可能来自同一 Sentinel product；尤其跨 split 有 13、6、5 个日期重合，不能排除同 scene 覆盖多个 parent。

## 停止原因和最小补救

继续使用文件名或 STAC date-only 搜索只会扩大候选集合而不会增加身份确定性，因此按停止条件结束历史 scene matching。最小补救按证据价值排序：

1. 从原作者恢复生成时的 `data.json` 和 UUID/download log。
2. 取得生成时版本的 CyAN GeoTIFF headers，并验证 transform/hash，而不是使用当前重处理产品冒充历史文件。
3. 用恢复后的 footprint 查询 STAC；再以产品 UUID、processing baseline、MGRS、timestamp 和 raster-content replay 交叉确认。
4. 最后与版本冻结的 NHDPlusHR waterbody polygons 相交。

在这些证据到位前，历史地理身份保持 `UNVERIFIED`。
