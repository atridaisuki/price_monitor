# Git 版本控制面试详解（第七部分强化版）

> 基于 `docs/study/interview-prep.md` 第七部分扩展，目标：达到后端实习/校招面试可直接作答标准

---

## 目录

- [一、先讲结论：面试官真正想听什么](#一先讲结论面试官真正想听什么)
- [二、Git 核心概念（必须讲清）](#二git-核心概念必须讲清)
- [三、常用命令（不止会背，要会解释）](#三常用命令不止会背要会解释)
- [四、标准团队工作流（重点）](#四标准团队工作流重点)
- [五、分支策略与 PR 规范](#五分支策略与-pr-规范)
- [六、冲突处理与回滚（高频追问）](#六冲突处理与回滚高频追问)
- [七、面试高频问答（可直接背）](#七面试高���问答可直接背)
- [八、结合你项目的回答模板（加分）](#八结合你项目的回答模板加分)
- [九、面试前 10 分钟速记清单](#九面试前-10-分钟速记清单)

---

## 一、先讲结论：面试官真正想听什么

面试官通常不是考你会不会 `git add`，而是看你是否具备：

1. **独立开发能力**：能用分支安全开发，不污染主分支。
2. **团队协作能力**：能通过 PR 合并，能处理冲突。
3. **风险控制能力**：知道何时用 `revert`，何时不能乱用 `reset --hard`。
4. **工程习惯**：提交信息规范、提交粒度合理、可回溯。

---

## 二、Git 核心概念（必须讲清）

### 2.1 Git 是什么？

Git 是**分布式版本控制系统**。每个开发者本地都有完整历史，不依赖单点服务器。

### 2.2 三个工作区域（必考）

```
Working Directory  ->  Staging Area  ->  Local Repository
   工作区                 暂存区               本地仓库
```

- 工作区：你正在改的文件
- 暂存区：本次要提交的“候选集”
- 本地仓库：已经形成历史提交

### 2.3 HEAD 是什么？

HEAD 是“当前检出的提交指针”，通常指向当前分支的最新提交。

### 2.4 commit 的本质

一次 commit = “某时刻项目快照 + 提交说明 + 父提交关系”。

> 面试加分回答：
> “Git 不是存差异文件的简单列表，本质是通过对象和引用管理快照历史，所以回滚和分支都比较高效。”

---

## 三、常用命令（不止会背，要会解释）

> 以下是你可以在面试中“命令 + 用途 + 场景”三连回答的版本。

### 3.1 基础命令

```bash
git clone <repo>
git status
git add <file>
git commit -m "message"
git push
git pull
```

- `git status`：先看状态，再操作（避免误提交）
- `git add <file>`：推荐按文件精确暂存，不要无脑 `git add .`
- `git pull`：本质是 `fetch + merge`（或 rebase，取决于配置）

### 3.2 分支相关

```bash
git branch
git checkout -b feature/xxx
git switch -c feature/xxx
git merge feature/xxx
```

- 新开发放 feature 分支
- 通过 PR 合并回 `master/main`

### 3.3 历史查看

```bash
git log --oneline --graph --decorate
git diff
git diff --staged
```

- `git diff`：看工作区改动
- `git diff --staged`：看将要提交的内容

---

## 四、标准团队工作流（重点）

你可以按这套流程回答“你平时怎么用 Git”：

### 4.1 典型流程

```bash
# 1) 切到主分支并更新
git checkout master
git pull origin master

# 2) 新建功能分支
git checkout -b feature/product-api

# 3) 开发 + 小步提交
git add app/routers/products.py
git commit -m "feat: add product list pagination"

# 4) 推送远程
git push -u origin feature/product-api

# 5) 提交 PR，Code Review 后合并
```

### 4.2 为什么不用直接在 master 开发？

- 避免主分支不稳定
- 方便 code review
- 便于回滚和追责定位

---

## 五、分支策略与 PR 规范

### 5.1 常见分支模型

1. **简化 GitHub Flow（实习常见）**
   - `master/main`：稳定分支
   - `feature/*`：功能分支
2. **Git Flow（中大型项目）**
   - `main`、`develop`、`feature/*`、`release/*`、`hotfix/*`

> 实习面试建议：先说你用简化模型，再补一句“了解 Git Flow”。

### 5.2 提交信息规范（建议）

```text
feat: add Steam product crawler endpoint
fix: handle empty price history response
refactor: split scraper parser logic
chore: update docker compose env
```

原则：
- 一次提交只做一件事
- message 描述“为什么改”而不只是“改了什么”

### 5.3 PR 描述模板（可复用）

- Summary：做了什么
- Why：为什么要改
- Test Plan：如何验证
- Risk：可能影响点

---

## 六、冲突处理与回滚（高频追问）

### 6.1 Merge Conflict 怎么处理？

标准回答步骤：

1. `git pull` / `git merge` 后出现冲突
2. 打开冲突文件，按业务逻辑手工合并
3. 删除冲突标记（`<<<<<<<` 等）
4. 重新 `git add` + `git commit`
5. 运行测试确认

### 6.2 `merge` vs `rebase`

- `merge`：保留分叉历史，安全直观
- `rebase`：让历史更线性、更干净

> 面试可答：
> “团队协作时我默认用 merge 保守合并；个人 feature 分支整理历史时会用 rebase，但不会 rebase 已共享给他人的公共提交。”

### 6.3 `reset` vs `revert`（非常高频）

- `git reset`：移动分支指针，可能改写历史
- `git revert`：新增一个“反向提交”，不改历史

规则：
- **已推送到远程公共分支**：优先 `revert`
- **本地未共享提交**：可用 `reset` 整理

---

## 七、面试高频问答（可直接背）

### Q1：`git pull` 和 `git fetch` 区别？

A：
- `fetch` 只拉远程更新到本地远程跟踪分支，不改当前工作分支。
- `pull` = `fetch + merge/rebase`，会尝试把更新合并到当前分支。

### Q2：为什么要有暂存区？

A：
- 让我们按“逻辑变更”组织提交。
- 可以在同一个工作区改很多内容，但只挑一部分先提交。

### Q3：你怎么保证提交质量？

A：
1. 先 `git diff --staged` 自检
2. 小步提交，控制粒度
3. 提交前跑测试
4. 走 PR + Code Review

### Q4：误删代码并提交了怎么办？

A：
- 如果已推远程并被别人使用：`git revert <commit>`
- 若只是本地提交且未共享：可 `git reset --soft HEAD~1` 后修正再提交

### Q5：你如何解决冲突？

A：
- 先理解双方改动意图，再合并，不是简单“保留我的/保留他的”。
- 合并后必须回归测试关键流程。

---

## 八、结合你项目的回答模板（加分）

你可以这样讲（面试可直接复述）：

> “在我的 Price Monitor 项目里，我会先从 `master` 拉最新代码，再切 `feature` 分支开发。比如做商品 CRUD 和 Steam 爬虫时，我按功能拆成多次提交，避免一个 commit 混入太多改动。开发完成后推送远程发 PR，重点让 reviewer 看 API 设计、数据库操作和异常处理。如果遇到冲突，我会先对比双方修改意图再手工合并，最后跑接口测试确认。对于已经推送的错误提交，我会优先使用 `revert` 保证团队历史安全可追溯。”

---

## 九、面试前 10 分钟速记清单

1. 说清三区：工作区 / 暂存区 / 本地仓库
2. 说清分支工作流：`master -> feature -> PR -> merge`
3. 说清冲突处理步骤
4. 说清 `fetch/pull`、`merge/rebase`、`reset/revert` 区别
5. 准备一个你项目中的真实 Git 协作案例

---

## 一句话总结（可作收尾）

> Git 面试拿高分的关键，不是背命令，而是展示你有**工程化协作意识**：可追溯、可回滚、低风险、适合团队开发。