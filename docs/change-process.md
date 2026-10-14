# 内容冻结后的变更流程

> 字库一旦「冻结」（即 M2 达成 scope 契约、CI 全绿、浏览站上线），
> 任何改动都必须走本流程。目的是：已发布的字条不因随手改一个解析就悄悄变化，
> 已发出去的分站快照与线上字库保持一致。

## 什么算「冻结后」

- M2 完成，`docs/scope.md` 收录清单稳定；
- CI 可复现闸门长期绿；
- `jiagu-site` 已部署、有用户在玩。

满足以上三条即视为冻结。冻结前（M0–M2）随手改、随手提交即可。

## 变更分级

| 级别 | 改动内容 | 流程 |
|---|---|---|
| **L0 勘误** | 错别字、断句、解析笔误（不改 id/char/字类/今字） | 改 md → 重跑 build/gen-index/build-site → 提交。CI 会重算 data/ 与索引，必须一致。 |
| **L1 字形换源** | 把某字的渲染图换成 S1 扫描图（或反之） | 改 `tools/gen-glyphs.py` 或直接放扫描图 → 重跑 gen-glyphs → 重算 checksums → 提交。 |
| **L2 增删字条** | 新增 / 删除一个字条 | 改 md + 同步 `docs/scope.md` 收录清单 → 重跑全链 → 提交。scope 清单必须与字条一一对应（validate 第 1 项）。 |
| **L3 改 id / char / 字类** | 改稳定标识或今字或主分类 | **禁止**。这会让已发布的快照与线上不一致。确需改的，走「删旧字 + 增新字」，并在 `PROVENANCE.md` 留痕。 |

## 每级变更的共同动作

1. 改内容（md / gen-glyphs.py / scope.md）。
2. 重跑链条：`python tools/build.py && python tools/gen-index.py && python tools/build-site.py`。
3. 跑护栏：`python tools/validate.py`、`node tools/check-legal.mjs`。
4. 提交前确认 `git status` 干净（可复现闸门）——提交的 data/、索引、站点副本必须与链条重算一致。
5. 推送后，**显式更新分站快照**：`cd ../jiagu-site && npm run sync:corpus`，看 diff，提交。
   不更新快照的话，分站仍是旧字库（这是刻意的——快照是单向的，内容仓改了不会自动波及分站）。

## 为什么 L3 禁止改 id/char

分站的每日题、历史记录都按 `id` 索引。改了 id 或 char，已发出去的「当日题」
就指向了另一个字，历史回放会错乱。所以 id 与 char 是**永久稳定标识**，
改字只能删旧增新，不能原地改。
