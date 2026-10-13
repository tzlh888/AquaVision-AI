# AquaVision 研究工件恢复报告

审计日期：2026-10-12  
恢复结论：**已从官方 Zenodo record file endpoint 精确恢复 288/288 个冻结 v2 CyAN reference arrays，并逐个通过 ZIP CRC/size/member 与历史 SHA-256 核验；Sentinel-2 arrays、模型和 prediction caches 仍未恢复。**

## 搜索范围

- 当前 AquaVision 工作目录、同日完整 Git-history audit 副本和其他本地仓库副本。
- 两个 Git commit（`03706fb`、`bd11ece`）及 tag `v1.0.0`。
- `.gitignore`、Git LFS（0 个 LFS objects）、raw/interim/processed、Phase 3/3.5/4/5 输出目录。
- Phase 3 pilot、Phase 3.5、Phase 4 delivery manifest 和 Phase 5 preservation manifest。
- Zenodo record snapshot、ZIP 索引日志、range acquisition 日志、v2 split 和 288 对历史数组哈希。

没有在本地找到 AquaVision 的 `.pt`、`.joblib` 或 `.npz` binary。完整 Git 历史也没有跟踪这些 ignored 文件。

## Phase 5 保存清单核验

Phase 5 preservation manifest 共 443 项：

| 当前状态 | 数量 | 解释 |
|---|---:|---|
| SHA-256 exact verified | 322 | 当前文件与历史保存哈希相同 |
| documented public-release sanitization | 7 | 当前哈希与 `public_release_sanitization.json` 的 after hash 相同；只清理了私人路径 |
| missing locally | 114 | 当前 checkout 无文件 |
| unexplained mismatch | 0 | 未发现未解释的哈希变化 |

114 个缺失项包含 23 个 checkpoint/joblib、43 个 Phase 4 `.npz` 文件、6 个 ZIP central-directory CSV，以及若干 ignored source snapshots、旧 metadata CSV 和 build metadata。43 个 `.npz` 中包括 40 个 validation/test prediction caches 与 3 个 integrated-gradient cache。

## v2 原始数组

v2 manifest 对 288 个样本保存了 288 个 Sentinel-2 SHA-256 和 288 个 CyAN reference SHA-256。本轮恢复后，288 个 CyAN arrays 均为 `VERIFIED`，288 个 Sentinel-2 arrays 仍为 `MISSING_LOCAL`。`ARTIFACT_PROVENANCE_MANIFEST.json` 逐条记录 source archive、member、archive MD5、期望 SHA-256、历史路径和重建条件。

原 Phase 3.5 acquisition summary 记录曾选择性取得 288 个 Sentinel 输入（28,348,416 content bytes）和更大 reference screening cache；这些历史日志证明当时曾存在，不等于当前文件已恢复。

## 恢复尝试

最初通过 Zenodo API content endpoint 对 `dataset_test.zip` 发起 4,313-byte 定向 Range 请求，返回 HTTP 504。随后改用同一 Zenodo record 的官方 file endpoint；首个成员经解码后与历史 SHA-256 精确相同，因此才执行受控批量恢复。共 12 个 multipart Range 请求覆盖 3 个 archive，没有下载完整 ZIP；所有响应必须为 HTTP 206，否则脚本立即退出。

恢复脚本 `recover_v2_cyan_arrays.py` 对每个成员执行：精确 offset/span、ZIP member name、compression、CRC32、uncompressed size、NumPy artifact bytes SHA-256 核验，并拒绝覆盖任何哈希不一致的已有文件。`CYAN_ARRAY_RECOVERY_LOG.json` 保存 288 条恢复记录。恢复内容是原始 deposit member 的逐字节复原，不是统计上相似的 reconstructed dataset。

推荐重建路径（仅数据，不训练）：

```text
python scripts/index_phase3_5.py
python scripts/prepare_phase3_5_pairs.py
```

Sentinel-2 arrays 的恢复仍需：Zenodo Range 服务可用；六个 archive 与 snapshot 的 size/MD5 一致；重建的 central-directory CSV 与历史记录一致；每个解码 member 的 CRC、shape、dtype 和最终 SHA-256 与 v2 manifest 一致。任何哈希不同的重建只能标为 reconstructed，不得替换 historical artifact。本轮没有仅凭文件名推断 Sentinel-2 offset。

模型和 prediction caches 不能通过数据下载恢复。checkpoint 只能通过找到原文件或重新训练得到；本阶段禁止训练，因此状态为 `MISSING_LOCAL / REQUIRES_ORIGINAL_FILE_OR_RETRAINING`。保存的 JSON/CSV confusion matrix 和指标仍可审计，但当前 checkout 不能完成独立 checkpoint reload 或逐像素 prediction replay。

## 可复现性边界

- **当前可复算/核验**：288 个 CyAN 标签数组及其像素标签、split membership、High support、历史 confusion matrices/metrics 表、选择规则、metadata/hash manifests、报告一致性。
- **当前不可复算**：缺少 288 个 Sentinel-2 arrays 和 checkpoint，故不能从 input pair 开始 inference；也不能 checkpoint reload、逐预测复现 40 个 cache 或复现 3 个 IG cache。
- **历史证据**：Phase 5 当时报告 100 个 confusion matrices、40 个 prediction caches 和 288 个 input-pair hashes exact；这是历史运行记录，不是本轮重新验证。

详细逐文件状态见 `ARTIFACT_PROVENANCE_MANIFEST.json`。

