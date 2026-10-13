# Sentinel-2 原始工件恢复报告

恢复日期：2026-10-12  
结论：**冻结 v2 的 288/288 个原始 Sentinel arrays 已 exact recovery。**

## 恢复方式

Phase 3.5 的 `pair_access.jsonl` 保存了当时成功取得 288 个 Sentinel ZIP members 的精确 byte ranges。该日志 SHA-256 为 `a645f61bddd89f05b42ab95c1ed767a0e3e022b1481da061eb0ec6e0dead2e0d`，与 Phase 5 preservation manifest 一致。

本轮使用官方 Zenodo record file endpoint，按该冻结范围执行 36 个 bounded multipart HTTP requests：

- 只接受 HTTP 206 和 identity encoding；HTTP 200 full-response fallback 被拒绝。
- 从 ZIP local header 验证 member name、compression、CRC32 和 uncompressed size。
- 解码结果逐项与 `geographic_split_v2.json` 的 Sentinel SHA-256 对比。
- existing mismatch 会退出，绝不覆盖。
- 没有下载完整 ZIP，没有训练模型。

## 恢复结果

| Archive | 数组数 | 状态 |
|---|---:|---|
| `dataset_test.zip` | 144 | exact bytes verified |
| `dataset_train_6_2.zip` | 48 | exact bytes verified |
| `dataset_train_6_5.zip` | 96 | exact bytes verified |
| 合计 | **288** | **288/288 verified** |

所有数组均符合冻结的 12×64×64 `uint16` 结构，合计约 28 MiB。详细来源、目标路径、大小和 SHA-256 见 `SENTINEL_ARRAY_RECOVERY_LOG.json`。

这是从原 Zenodo archive 恢复的历史 artifact，不是重新从 Copernicus 生成的 reconstruction。因此无需声称当前 STAC 产品与历史输入等价。

## 仍然缺失的元数据

NPY header 只保存 shape/dtype，不包含：

- Sentinel product UUID/ID、MGRS、sensing timestamp 或 processing baseline；
- CRS、affine transform、parent crop window 或 actual footprint；
- 原始 band asset identifiers；
- waterbody identity。

所以 exact arrays 提升了输入数据复现能力，但没有自动修复 geographic provenance。模型 checkpoint 和 prediction caches 也未因本次恢复而出现。

## 重运行

恢复脚本为 `recover_v2_sentinel_arrays.py`。再次运行只会接受并登记已经与冻结 SHA-256 相同的文件；任何不一致都会停止。
