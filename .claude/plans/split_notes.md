# 全 Vault 文档拆分分析报告

> 共扫描 38 篇笔记（含 5 个索引页），按大小、章节数、逻辑独立性分析。

---

## 🔴 强烈建议拆分（>100KB 或 多章节/多天）

| 文件 | 大小 | 拆为 |
|------|:--:|------|
| **SSM框架/Spring框架.md** | 243KB | `Spring框架/` 文件夹：`day01-IOC与DI.md` / `day02-AOP.md` / `day03-事务.md` |
| **JavaWeb/01-Web前端基础.md** | 235KB | `Web前端/` 文件夹：`HTML与CSS.md` / `JavaScript.md` / `Ajax与Vue.md` / `Element.md` |
| **JavaWeb/05-SpringBootWeb案例与登录认证.md** | 184KB | 拆为同目录下：`案例-员工管理(上).md` / `案例-员工管理(下).md` / `登录认证.md` |
| **SSM框架/SpringMVC.md** | 164KB | `SpringMVC/` 文件夹：`day01-基础.md` / `day02-高级.md` |
| **JavaSE/09-常用API.md** | 159KB | 拆为同目录下：`Math与System.md` / `正则表达式.md` / `时间与包装类.md` / `算法与Lambda.md` |
| **MySQL/MySQL-进阶篇.md** | 156KB | `进阶篇/` 文件夹，按 7 章拆为 7 个子文件 |
| **Redis/Redis-实战篇.md** | 156KB | 拆为同目录下：`短信登录.md` / `商户查询缓存.md` / `优惠券秒杀.md` / `达人探店.md` 等 |
| **Redis/Redis-高级篇.md** | 130KB | `高级篇/` 文件夹：`分布式缓存.md` / `多级缓存.md` / `最佳实践.md` / `集群.md` |

## 🟡 可选拆分（50-100KB，1-2个章节边界）

| 文件 | 大小 | 说明 |
|------|:--:|------|
| JavaSE/05-面向对象编程.md | 94KB | 拆分价值高：`OOP基础.md` / `static与继承.md` / `多态.md` / `抽象与接口.md` |
| JavaSE/06-面向对象综合练习.md | 86KB | 拆为 `格斗游戏.md` / `拼图游戏.md` / `键盘录入附录.md` |
| JavaSE/11-IO流.md | 100KB | 拆为 `异常与File.md` / `字节与字符流.md` / `其他流.md` |
| JavaSE/12-多线程.md | 97KB | 拆为 `线程基础.md` / `JUC并发.md` |
| JavaSE/10-集合框架.md | 62KB | 拆为 `Map与可变参数.md` / `Stream与方法引用.md` / `斗地主项目.md` |
| JavaWeb/02-数据库与持久层.md | 90KB | 拆为 `MySQL多表查询.md` / `Mybatis入门.md` / `Mybatis基础.md` |
| MySQL/MySQL-基础篇.md | 95KB | 按 6 章拆分 |
| MySQL/MySQL-运维篇.md | 91KB | 按 4 章拆分 |
| SSM框架/MyBatisPlus.md | 82KB | 拆为 `基础CRUD.md` / `条件查询.md` / `插件与扩展.md` |
| Redis/Redis-入门篇.md | 76KB | 拆为 `NoSQL与Redis安装.md` / `5种数据类型.md` / `Jedis客户端.md` |

## 🟢 保持现状（<50KB 或 内容紧凑不可拆）

JavaSE: 01~04, 07, 08, 13, 14 — 共 8 篇
JavaWeb: 04, 06, 07, 08 — 共 4 篇
SSM框架: SpringBoot.md (49KB)
Redis: Redis-原理篇.md (57KB)
MySQL: — （三篇全部建议拆）

---

## 📊 汇总

| 模块 | 总篇数 | 建议拆分 | 可选拆分 | 保持 |
|------|:--:|:--:|:--:|:--:|
| JavaSE | 15 | 1 | 5 | 9 |
| JavaWeb | 9 | 2 | 1 | 6 |
| MySQL | 4 | 3 | 0 | 1(索引) |
| SSM框架 | 5 | 2 | 1 | 2 |
| Redis | 5 | 2 | 1 | 2 |
| **合计** | **38** | **10** | **8** | **20** |

## 🔧 拆分时需要注意

1. `---` 分隔符后的 footer（`> 📎 **相关笔记**`）是导航栏，不是内容章节
2. 所有图片已用 `file:///` 绝对路径，拆到子文件夹不影响渲染
3. 拆分后需更新索引页和各笔记间的 `[[wikilink]]` 链接
4. MySQL 三篇的 `---` 来自表格语法（`| --- |`），不能作为拆分边界——需按 `##` 章节标题拆
