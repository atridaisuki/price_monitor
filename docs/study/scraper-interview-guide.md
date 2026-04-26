# 爬虫与反爬面试详解（第八部分强化版）

> 基于 `docs/study/interview-prep.md` 第八部分扩展，目标：达到后端实习/校招面试可直接作答标准

---

## 目录

- [一、面试官在第八部分想考什么](#一面试官在第八部分想考什么)
- [二、你项目中的爬虫架构（必须能讲）](#二你项目中的爬虫架构必须能讲)
- [三、Steam 抓取流程拆解（按执行链路）](#三steam-抓取流程拆解按执行链路)
- [四、反爬基础与项目实践](#四反爬基础与项目实践)
- [五、异常设计与故障定位（高频追问）](#五异常设计与故障定位高频追问)
- [六、可扩展性设计：如何新增平台](#六可扩展性设计如何新增平台)
- [七、面试高频问答（可直接背）](#七面试高频问答可直接背)
- [八、结合你项目的标准回答模板](#八结合你项目的标准回答模板)
- [九、面试前速记清单](#九面试前速记清单)

---

## 一、面试官在第八部分想考什么

不是单纯问“你会不会 BeautifulSoup”，而是看你是否具备：

1. **抓取链路理解**：请求、解析、提取、清洗、异常处理。
2. **工程意识**：模块化、可扩展、可维护。
3. **边界意识**：反爬对抗是持续博弈，能否稳定处理失败场景。
4. **合规意识**：遵守目标站点协议、频率控制、避免滥用。

---

## 二、你项目中的爬虫架构（必须能讲）

结合当前代码，结构清晰：

- `app/scrapers/base.py`：抽象基类 `BaseScraper`
- `app/scrapers/steam.py`：`SteamScraper` 具体实现
- `app/scrapers/exceptions.py`：自定义异常分层
- `app/scrapers/__init__.py`：`SCRAPER_MAP` + `get_scraper()` 工厂入口

### 2.1 为什么这样设计？

因为你用了**“抽象接口 + 平台实现 + 工厂选择”**的标准模式。

优点：
- 新平台扩展成本低
- 路由/业务层无需关心具体抓取细节
- 统一异常类型，方便上层处理

### 2.2 面试可直接说的架构句子

> “我把爬虫设计成可插拔结构：`BaseScraper` 规定统一接口，`SteamScraper` 实现具体平台逻辑，`get_scraper()` 根据平台或 URL 动态返回实例，新增平台时只需新增一个子类并注册映射，不需要改上层业务代码。”

---

## 三、Steam 抓取流程拆解（按执行链路）

### 3.1 调用入口

- `get_scraper(platform_or_url)` 负责选择平台实现（`app/scrapers/__init__.py:12`）
- 返回 `SteamScraper` 实例后调用 `scrape(url)`（`app/scrapers/steam.py:25`）

### 3.2 `scrape` 的主链路

1. URL 校验：`is_valid_url()`（`app/scrapers/steam.py:21`）
2. 拉取页面：`_fetch_page()`（`app/scrapers/steam.py:42`）
3. 解析价格：`_parse_price()`（`app/scrapers/steam.py:57`）
4. 文本转数字：`_extract_price_number()`（`app/scrapers/steam.py:79`）

### 3.3 关键实现亮点

- 使用 `httpx.AsyncClient` 异步请求，适配 FastAPI 异步栈（`app/scrapers/steam.py:52`）
- 使用 `BeautifulSoup(..., "lxml")` 做 DOM 解析（`app/scrapers/steam.py:59`）
- 价格选择器采用优先级列表，先折扣价再原价（`app/scrapers/steam.py:16`）
- 使用正则提取数值并统一清洗货币符号（`app/scrapers/steam.py:82`）

---

## 四、反爬基础与项目实践

### 4.1 你当前已经做了什么

在 `_fetch_page` 里设置了浏览器 `User-Agent`（`app/scrapers/steam.py:44`）。

这属于反爬最基础的一层：避免默认客户端特征过于明显。

### 4.2 面试要讲清的反爬手段（分层）

1. **请求头伪装**：`User-Agent`、`Accept-Language`、`Referer`
2. **访问频率控制**：限速、抖动延迟、退避重试
3. **身份维持**：Cookie / Session
4. **网络层策略**：代理池（合规前提下）
5. **页面层对抗**：动态渲染、JS 混淆、验证码

### 4.3 如何回答“如何避免被封？”

推荐回答：

> “我的原则是优先合规和稳定，而不是激进绕过。实践上会先做合理请求头、频率控制和错误重试，再根据业务需要评估 Cookie/代理。对于验证码或强对抗场景，一般会评估是否改为官方 API 或合作数据源。”

---

## 五、异常设计与故障定位（高频追问）

你项目的异常分层非常适合面试：

- `FetchException`：网络请求失败（`app/scrapers/exceptions.py:9`）
- `ParseException`：结构变化或解析失败（`app/scrapers/exceptions.py:14`）
- `PriceNotFoundException`：页面可访问但价格节点未命中（`app/scrapers/exceptions.py:19`）

### 5.1 为什么分层异常有价值？

- 上层可以按错误类型采取不同动作
- 便于监控和告警分类
- 有利于快速定位根因（网络问题 vs 页面结构变更）

### 5.2 典型排障流程（可背）

1. 先看是否 `FetchException`（网络/超时/HTTP 状态）
2. 再看 `PriceNotFoundException`（选择器失效）
3. 最后看 `ParseException`（文本格式异常）

---

## 六、可扩展性设计：如何新增平台

当前项目已经具备可扩展骨架。

### 6.1 新增平台标准步骤

1. 新建 `NewPlatformScraper(BaseScraper)`
2. 实现 `is_valid_url()` 与 `scrape()`
3. 平台内部实现 `_fetch_page()`、`_parse_price()`
4. 在 `SCRAPER_MAP` 注册平台映射（`app/scrapers/__init__.py:7`）

### 6.2 面试加分表达

> “我把平台差异封装在各自 Scraper 子类里，对外暴露统一 `scrape(url)`。这种方式让业务层与平台细节解耦，扩展新平台时影响面很小，符合开闭原则。”

---

## 七、面试高频问答（可直接背）

### Q1：`requests` 和 `httpx` 的区别？

A：
- `requests` 主要是同步库。
- `httpx` 同时支持同步/异步，异步场景下可与 FastAPI 协程链路一致，吞吐更好。

### Q2：为什么要用抽象基类？

A：
- 统一接口，防止子类遗漏关键方法。
- 让工厂函数返回统一类型，便于上层调用。

### Q3：页面结构变化导致抓取失败怎么办？

A：
- 先通过日志判断是请求失败还是解析失败。
- 若是解析失败，更新选择器并补充回归测试样例。

### Q4：为什么价格提取不能只做 `float(text)`？

A：
- 页面价格常带货币符号、空格、千分位，需要先做清洗再转换。

### Q5：如何保证爬虫稳定性？

A：
- 超时控制、异常分类、重试策略、监控告警、回归测试、限速策略。

---

## 八、结合你项目的标准回答模板

> “我的价格抓取模块采用可扩展架构：先通过 `get_scraper()` 选择平台实现，再调用统一 `scrape(url)` 接口。以 Steam 为例，先校验 URL，再异步请求页面，最后通过 `BeautifulSoup + CSS 选择器 + 正则` 提取价格数字。错误处理上我做了分层异常，比如请求失败、解析失败、价格未命中分开处理，这样上层可以精确告警和降级。后续如果新增平台，只需要新增 Scraper 子类并注册映射，不影响现有业务流程。”

---

## 九、面试前速记清单

1. 讲清接口：`BaseScraper.scrape()` + `is_valid_url()`
2. 讲清工厂：`get_scraper()` + `SCRAPER_MAP`
3. 讲清链路：校验 URL → 拉页面 → 解析 DOM → 提取价格
4. 讲清异常：`Fetch` / `Parse` / `PriceNotFound`
5. 讲清扩展：新增子类 + 注册映射

---

## 一句话总结

> 第八部分拿高分的关键是：不仅会“抓到数据”，还要展示你有**工程化爬虫思维**——可扩展、可观测、可维护、合规稳定。
