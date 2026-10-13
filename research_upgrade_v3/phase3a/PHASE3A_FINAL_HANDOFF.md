# AquaVision Phase 3A Final Handoff

日期：2026-10-12  
最终状态：**NOT READY**  
模型训练：**未发生**  
历史文件修改：**无**  
Git commit / push：**均未执行**

## 最终判定

AquaVision 的 processed-CyAN proxy 标签、288 条 v2 成员身份及全部 288 个 CyAN arrays 已恢复并可逐哈希复核；author-grid component 级 split 隔离也得到复核。但是 scene/product、lake/waterbody、CRS/footprint 和 bloom-event 身份没有恢复，Validation 只有 1 个 High candidate component，Sentinel-2 arrays/checkpoints/prediction caches 仍缺失。因此仍不具备可信 Phase 3B 模型选择和跨地域泛化评估条件。

## A–L 回答

**A. High 标签来自什么？** 来自日级 NASA CyAN `CI_cyano` 经重投影、双线性重采样、Sentinel-derived cloud/land masking 和 patch 切分后的 stored DN；DN 200–253 映射为 High。

**B. 科学可信性如何？** 对复现“Sentinel-2→processed CyAN proxy bin”有中等、受限可信性；对现场细胞数、毒素、健康危险或真实 20 m 生物标签没有直接验证。

**C. Validation/Test 有多少独立地点、scene、水体？** 可确认的 author-grid component 为 1/3；可确认的独立 lake、scene、waterbody 和 bloom event 数量均为 `UNVERIFIED`，不能把 1/3 component 改写为真实地点数。

**D. 是否有跨 split 重复？** sample、component、subtile、patch-position candidate 和 Sentinel array hash 均无重叠。每对 split 共享一个全 Low reference 内容哈希，日期也有重合；scene/footprint overlap 因身份缺失无法判断。

**E. 恢复多少原始工件？** 本轮新恢复 288 个 CyAN binary arrays，全部与冻结 SHA-256 一致。443 项历史保存清单中 322 项当前 exact verified，7 项匹配已记录的公开发布路径清理，114 项缺失；v2 的 288 个 Sentinel-2 arrays 仍缺失。逐项 provenance/hash 已登记到新 manifest。

**F. 原选择规则问题？** 以 validation Macro-F1 为 primary，只给 Low/Moderate 设门槛，没有 High Recall/High F1 hard gate，因此 High F1=0 的 NDCI 仍可成为 winner；Validation 又只有一个 High component。

**G. 新机制？** 先执行 verified geography/scene/data gate；再要求 High Recall≥0.50、High F1≥0.50、Low F1≥0.50、Moderate F1≥0.40、Macro-F1≥0.50、每 High component recall>0。首要排序为 equal-component mean High F1，并设 `NO QUALIFIED MODEL` 退出。

**H. 能否找到新独立 High 样本？** 找到可行来源和重建路线，但尚未得到通过身份、重叠和 support gate 的 sealed 独立样本。公开数据可行不等于样本已合格。

**I. 是否具备可信训练条件？** 否。技术上可继续做明确标记的探索性工作，但当前连 exploratory v3 的预先数据门槛也未满足，不建议训练。

**J. 最大质量问题？** 有效独立 High 验证单元不足且身份缺失：大量相关像素不能替代独立 lake/scene/event；这比继续优化模型架构更根本。

**K. 已解决与限制？** 已解决标签 DN 映射、288 条 patch 身份与 CyAN array 恢复、candidate-component split isolation、High support 集中度、artifact 状态和未来资格规则。仍未解决逐样本 product/scene/lake/footprint/event、适用 CyAN processing version、物理配准复核、Sentinel/model/prediction binary artifacts 和外部现场验证。

**L. 是否建议 Phase 3B？** **不建议。** 先完成 metadata/array 恢复与至少 3 个 verified High Validation units（最好达到 ≥10 以支持 cluster uncertainty）、独立 Test sealing，再训练才不会把模型优化建立在伪独立证据上。

## 验收结果

- 真实 v2 身份表：288 行。
- High group support：38 个 screened candidate components，其中 6 个进入 v2；完整 screening 不是 full-deposit prevalence。
- split overlap 审计：36 行，包含已验证、candidate 和 `UNVERIFIED` 类型。
- 自动化测试：10/10 通过；7 个逻辑/异常单元测试 + 3 个真实 v2 integration tests（包括 288 个恢复数组逐哈希验证）。
- Artifact：322/443 exact、7/443 documented sanitization、114/443 missing；v2 arrays 为 288/576 verified、288/576 missing。
- Remote recovery：API content endpoint 曾返回 HTTP 504；官方 record file endpoint 随后以 12 个受控 HTTP 206 请求精确恢复 288 个 CyAN arrays，未下载完整 ZIP。
- 历史结果：NDCI/LR/RF/CNN、失败模型和 LIMITED 结论均未改写。

## 证据保护与 Git 状态

| 项目 | 分支 | HEAD | 开始状态 | 完成状态 |
|---|---|---|---|---|
| AquaVision | `research-upgrade-v3` | `bd11eceaa7efa7ca785d5e466cf807312ed70df0` | 5 个 Phase 2A untracked files；porcelain SHA-256 `78e95b475e9c840ad1a2695aa7b3e28357b2685ed34ae198cb5af60deb193c1a` | 20 个 untracked files（原 5 + Phase 3A 15）；porcelain SHA-256 `b585d615fe348e91b97ff16cb51eb7e3391cf8fb33d31797889fc906c42079ca` |
| WaterSense | `research-upgrade-v3` | `3553b29ff104918b12da8c84d2c9a8c5ed032e18` | 131 个 untracked files；porcelain SHA-256 `1ad752764355498fe02f2c6762ce23b561e3aca7dd04049541819eed29f2de25` | 完全相同；未修改 |

AquaVision 与 WaterSense 的 tracked diff 和 staged diff 均为空。没有移动、删除或覆盖已有 untracked 研究文件。288 个恢复数组位于被历史 `.gitignore` 排除的 `data/raw/phase3_5_references/`（约 2.3 MiB），因此不计入 20 个 untracked paths，也不会意外进入公共仓库。

开始前 5 个 AquaVision Phase 2A 文件的 SHA-256 分别为：`EVIDENCE_MANIFEST.csv` `d22d16d8...d1b78c`、`LEGACY_BENCHMARK_REGISTRY.md` `a447ca7d...e809b`、`PHASE2A_IMPLEMENTATION_REPORT.md` `5df1afc5...fb09`、`PROTOCOL_FREEZE.md` `9b58fe06...1bead7`、`RESEARCH_DECISION_LOG.md` `4ab97aae...01cb7`；完成时复核仍相同。

## Phase 3A 文件哈希检查

| 文件 | SHA-256 |
|---|---|
| `ARTIFACT_PROVENANCE_MANIFEST.json` | `794ce4c8b04a3c76c11485c06564f3129715f3e11b4578cfb11b6759d123398d` |
| `ARTIFACT_RECOVERY_REPORT.md` | `7d164d776c711afef3a348153ffbdfae221607eb46fc06ee2501af7b89e166f0` |
| `CYAN_ARRAY_RECOVERY_LOG.json` | `97f672e82c253fa19a6cb3785b2d8c4bd4c74c3ef531a47e837bc16c7244ac54` |
| `EXPLORATORY_V3_SELECTION_PROTOCOL.md` | `e82562b9a8fd6f4591de9e258191e9f0341be5d49ba68fdade17452cb29e5c88` |
| `GEOGRAPHIC_IDENTITY_TABLE.csv` | `64430b72a5b5bfc4f54b7f8c4c5c9d139d734dd083385e1e076eb19362b1beeb` |
| `HIGH_CLASS_INDEPENDENCE_REPORT.md` | `37db11e0348d7487b59b4b77cbedd05208b90e645b70c028356ea7fe8bef3c76` |
| `HIGH_CLASS_PROVENANCE_AUDIT.md` | `b3832e194c7197b0b9596a7e1a6fd4068c1cf11a539762a0d1b4cae11cbbf3cd` |
| `HIGH_SUPPORT_BY_GROUP.csv` | `4e9cd348fa7e30377b1f751fff310d3a1af0f066707d399e606b30d5922216db` |
| `INDEPENDENT_DATA_FEASIBILITY.md` | `ae67a66a0eb49bbc3360d495110c741cab5d10439725811562dec8c99226c80e` |
| `SPLIT_OVERLAP_AUDIT.csv` | `69ccac1764444b3807498bb277d8423a29a20773e9015ebab5942dea54d67a5b` |
| `generate_phase3a_evidence.py` | `c371409845d03339ec0175f0456fbf8431330276cd099eae6bf36ce795187f92` |
| `phase3a_audit.py` | `88af72f0cdae1d81836d583a94e18ba874c366955572749ce977ae70225712f9` |
| `recover_v2_cyan_arrays.py` | `e51e8b15a6bc26df02296de4da4d5ad9f03408cd96baca232424472da8266d26` |
| `test_phase3a_audit.py` | `f5b88ff6145cb64cd6e8994fe053af9eabdeab74dcc8846e672358077673f26a` |

`PHASE3A_FINAL_HANDOFF.md` 的自哈希在外部最终验收中计算，避免文档自引用循环。

## 交付文件

1. `HIGH_CLASS_PROVENANCE_AUDIT.md`
2. `HIGH_CLASS_INDEPENDENCE_REPORT.md`
3. `GEOGRAPHIC_IDENTITY_TABLE.csv`
4. `SPLIT_OVERLAP_AUDIT.csv`
5. `ARTIFACT_RECOVERY_REPORT.md`
6. `ARTIFACT_PROVENANCE_MANIFEST.json`
7. `HIGH_SUPPORT_BY_GROUP.csv`
8. `EXPLORATORY_V3_SELECTION_PROTOCOL.md`
9. `INDEPENDENT_DATA_FEASIBILITY.md`
10. `PHASE3A_FINAL_HANDOFF.md`
11. `phase3a_audit.py`
12. `generate_phase3a_evidence.py`
13. `test_phase3a_audit.py`
14. `recover_v2_cyan_arrays.py`
15. `CYAN_ARRAY_RECOVERY_LOG.json`

完成后停止；不得自动开始 Phase 3B。

