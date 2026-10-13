# AquaVision Phase 3A-1 Final Handoff

日期：2026-10-12  
模型训练：**未发生**  
历史输出修改：**无**  
Git commit / push：**均未执行**

## 三项最终状态

| 判断对象 | 状态 | 证据 |
|---|---|---|
| A. Historical geographic identity recovery | **NOT READY** | 0/288 confirmed footprints、0/288 scenes、0/288 waterbodies；原 `data.json`/UUID/transform 不在公开 artifacts 中 |
| B. Prospective independent dataset construction | **CONDITIONALLY READY** | 官方 STAC、CyAN、USGS 来源和防污染协议可用，但尚无通过全部 identity/support/overlap gate 的 unit |
| C. Phase 3B model experimentation | **NOT READY** | Validation 仍只有 1 个 legacy High component；0 个 prospective qualified Validation units，0 个 sealed Confirmation units |

## 最终问题回答

**1. 288 个历史 patch 中多少恢复了可信真实位置？** **0**。288 个均恢复了日期、author-grid parent 和相对 array window，但没有 CRS/affine/original crop window，故不能生成 actual footprint。

**2. 多少恢复了 Sentinel scene 身份？** **0**。288 个原始 Sentinel arrays 已恢复，但 NPY 不含 product ID；上游 `sen2_uuid` 被传入 `save_data` 后未保存。官方 STAC date-only search 不具唯一识别性。

**3. 多少恢复了真实 waterbody 身份？** **0**。没有可靠 footprint 可用于 NHDPlusHR intersection；没有从 component 或图像猜测 lake ID。

**4. 是否确认任何跨 split 的实际空间重复？** **没有确认，也不能排除。** sample/component/parent/Sentinel hash 没有跨 split 重叠；actual footprint、same lake、same scene 全部不可计算。日期跨 split 重合且同一产品可能覆盖多个 parent。

**5. 原始 Sentinel arrays 恢复多少？** **288/288 exact recovery**。144 Test、48 train-6_2、96 train-6_5；全部验证 ZIP member/CRC/size 和冻结 SHA-256。恢复的是原 artifact，不是 reconstruction。

**6. CyAN processing version 是否证实？** **否。** 产品命名和处理代码已核实，V5 只是时间上合理的 candidate；没有原始 GeoTIFF checksum/version metadata，不能升为 CONFIRMED。

**7. 能否构建新的独立 High validation units？** 技术路线可行，但当前合格数为 **0**。12 个旧 deposit High-bearing candidates 都已做过 label screening，并缺少 waterbody/scene/footprint/version，不能进入 prospective Validation。

**8. 是否具备锁定 independent confirmation set 的条件？** 协议已具备，实际数据尚不具备。必须先构建新的 metadata-first catalog、完成污染图和 support census，再在任何模型训练前 seal confirmation manifest。

**9. 已消除哪些障碍？** Sentinel 与 CyAN 两侧 288+288 arrays 均已 exact verified；相对 patch window、split、High support、artifact provenance 和未来防污染规则可自动复算；官方 STAC 可访问性已核验。

**10. 哪些限制仍无法解决？** 历史 product UUID、timestamp、MGRS、source transform、actual footprint、waterbody、CyAN version、物理 overlap 和 bloom-event identity；checkpoint/prediction caches 也仍缺失。

**11. 是否值得继续投入 AquaVision？** **值得有限继续投入证据工程，不值得立即投入模型优化。** 首选向原作者索取 `data.json`/UUID logs；若不可得，则建立完全新的 prospective dataset。继续在 v2 上增加模型复杂度的边际科学价值低。

**12. 下一阶段最小必要工作？**

1. 尝试一次范围明确的作者 metadata recovery；失败即永久标记 historical geography unrecoverable。
2. 冻结 CyAN version、Sentinel collection/baseline、NHD release、matchup/event-window/buffer。
3. 建立 metadata-only candidate catalog，并验证 product/footprint/waterbody 与 legacy overlap。
4. 完成 label support census，达到至少 3 个合格 High Validation units，目标≥10。
5. 在训练前 seal 独立 Confirmation set；然后才重新判断 Phase 3B。

## 自动化与完整性验收

- 新增测试：11/11 通过，包括 evidence level、scene candidate、affine footprint、CRS intersection、temporal duplicate、conservative grouping、candidate rejection、ZIP local header、hash verification，以及真实 288-array/catalog integration。
- `PATCH_IDENTITY_CATALOG.csv`：288 行；Sentinel/CyAN artifacts 均 288 verified；confirmed footprint/scene/waterbody 均为 0。
- `INDEPENDENT_HIGH_CANDIDATES.csv`：12 行；qualified Validation 0，qualified Confirmation 0。
- UTF-8、JSON、CSV schema/row consistency 和私人绝对路径扫描通过。
- AquaVision/WaterSense tracked diff 与 staged diff 均为空。

## Git 证据保护

| 项目 | 分支 | HEAD | 开始状态 | 完成状态 |
|---|---|---|---|---|
| AquaVision | `research-upgrade-v3` | `bd11eceaa7efa7ca785d5e466cf807312ed70df0` | 20 untracked，status SHA-256 `b585d615fe348e91b97ff16cb51eb7e3391cf8fb33d31797889fc906c42079ca` | 35 untracked，status SHA-256 `8dd57f9e99e4c12d93962b32626af88329166ff5f5ce10680fcab170616046e6` |
| WaterSense | `research-upgrade-v3` | `3553b29ff104918b12da8c84d2c9a8c5ed032e18` | 131 untracked，status SHA-256 `1ad752764355498fe02f2c6762ce23b561e3aca7dd04049541819eed29f2de25` | 完全相同；未修改 |

Phase 2A 和 Phase 3A 的 20 个 AquaVision untracked 文件逐路径、逐哈希保持不变。新恢复 Sentinel arrays 位于历史 `.gitignore` 排除的 `data/raw/phase3_5_pairs/`，约 28 MiB，不会意外加入公共仓库。

## Phase 3A-1 文件 SHA-256

| 文件 | SHA-256 |
|---|---|
| `CYAN_PROCESSING_VERSION_AUDIT.md` | `1eb4012930c624939c6e4badd253ebecb182719370bb9ddcb324bc6e8098c531` |
| `GEOGRAPHIC_METADATA_RECOVERY.md` | `c11b859113e5730faaca4e515e9d7f266a0166065b07fcd092a2aefc87990838` |
| `INDEPENDENT_HIGH_CANDIDATES.csv` | `f9aa0f1dbd10eafb4d3f8382e77da7e00e6665a30f975ec06dec74e61da54f9a` |
| `PATCH_IDENTITY_CATALOG.csv` | `7a26f282e1dc4d738a813ef03a2de721da015ef394567d2180fc4d0b4a5e26db` |
| `PHYSICAL_OVERLAP_AUDIT.md` | `91d2a9085a16a3d8fbb7ea8b96c091b2cb8db6e89fdd8ec6c913775948a2acce` |
| `PROSPECTIVE_V3_DATASET_PROTOCOL.md` | `9310e0bf3ce9e16442e3f37ff7f0306555f4c231774fb6f027e9f2698dd0c956` |
| `SCENE_MATCHING_EVIDENCE.csv` | `aab6bb421c02c79703537885dd1433230646f462b8846528022354549447d19a` |
| `SENTINEL_ARRAY_RECOVERY_LOG.json` | `235926deb28411f7406c49d3a1b093527cdfd748cdea09b567da0f17688a7a10` |
| `SENTINEL_ARTIFACT_RECOVERY.md` | `ea65ce7371614779e8eb3b5c646bd33f06cbdc5c26ec2ddd48b79bf41424ad5d` |
| `WATERBODY_MATCHING_EVIDENCE.csv` | `ed159f0f374b3e2c206070baeb4bde072b8dd7f2a1bceae86c5762113a58f252` |
| `generate_phase3a1_catalogs.py` | `020ccdca02b3be5ad3f170a5b06ed818e347791bf0bc92efb4deb1d356f58076` |
| `phase3a1_audit.py` | `0d408f9514aa75235d4a177e9f4dce8b9474671601e6e68f32b0646a0b51bd9a` |
| `recover_v2_sentinel_arrays.py` | `91b3031d44adbcdbf9ce9226dbd61625cb5b29fc27a372cc31e976f03d8e28bf` |
| `test_phase3a1_audit.py` | `0134d961b49bca90e83d970b0fd74d4f6f2552232c6552aa75ae09d6026c4b62` |

`PHASE3A1_FINAL_HANDOFF.md` 自哈希在外部最终验收中计算，以避免自引用循环。

## 新增文件

1. `GEOGRAPHIC_METADATA_RECOVERY.md`
2. `PATCH_IDENTITY_CATALOG.csv`
3. `SCENE_MATCHING_EVIDENCE.csv`
4. `WATERBODY_MATCHING_EVIDENCE.csv`
5. `PHYSICAL_OVERLAP_AUDIT.md`
6. `SENTINEL_ARTIFACT_RECOVERY.md`
7. `CYAN_PROCESSING_VERSION_AUDIT.md`
8. `INDEPENDENT_HIGH_CANDIDATES.csv`
9. `PROSPECTIVE_V3_DATASET_PROTOCOL.md`
10. `PHASE3A1_FINAL_HANDOFF.md`
11. `SENTINEL_ARRAY_RECOVERY_LOG.json`
12. `phase3a1_audit.py`
13. `generate_phase3a1_catalogs.py`
14. `recover_v2_sentinel_arrays.py`
15. `test_phase3a1_audit.py`

完成后停止；不得自动开始 Phase 3B。
