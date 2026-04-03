# 题材化写作技巧与短对照范文

> 用途：作为题材导航索引，帮助按题材补读更小的写法文件。
> 原则：先用主技能保证结构与节奏，再按题材特性补强爽点、情绪点、冲突形态与语言节拍。

具体题材正文已拆到 `templates/genres/`，原有内容没有删除，只是不再一次性整块加载。

---

## 🛑 核心铁律：三级防冲突覆写协议 (Override Protocol)

当遇到由于系统库过于庞大导致的“节奏与文风冲突”时，**必须绝对遵守**以下优先级梯队：

- **🥇 第一层级（绝对优先级）：作家指纹库 & 具体题材库**
  - 风格指纹（如考据机锋档、群像悲壮档）的句式、意境要求，**无条件推翻**通用的“全短句、全快打脸”润色要求。
  - 特殊题材（如克苏鲁怪谈、历史权谋）的慢热、压抑或求生要求，**无条件推翻**通用自检中的“主角必须获得资源、升级”的标准。
- **🥈 第二层级（中优）：本章/本卷大纲目标**
  - 如果大纲写了“本章极尽憋屈”，则执行大纲，无视通用的“三章必扬”爽感公式。情节逻辑 > 通用爽点公式。
- **🥉 第三层级（保底基线）：全局写作指南与飞书知识摘要**
  - 只有在指纹和具体大纲没有特殊规定的“日常白板过渡章”里，才调用底层的快节奏爽文公式填补空白。

---

## 主副题材混合规则

当一本书不是单一题材时，默认按以下规则处理：

- **主题材**决定整体节奏、主要反馈类型、主线承诺
- **副题材**决定局部桥段、情绪包装、某些章节的表达方式
- 默认只建议 **1 个主题材 + 1 个副题材**，避免题材过多导致卖点失焦
- 若两个题材要求冲突，优先保留主题材的节奏与主反馈路径
- `/一键开书` 时先回答：这本书读者主要是为什么点进来；这个答案对应的就是主题材

### 混合示例

- 都市 / 系统流 + 直播 / 文娱 / 娱乐圈：主题材通常是“都市 / 系统流”，直播与文娱负责放大反馈与围观感
- 玄幻 / 修仙 + 轻喜剧 / 沙雕：主题材通常是“玄幻 / 修仙”，轻喜剧负责缓冲气氛和加强人物互动
- 宫斗 / 宅斗 + 仙侠恋爱 / 古言甜虐：主题材看主卖点；若主打情感拉扯，古言甜虐为主；若主打局中局与反制，宫斗宅斗为主
- 末世 + 校园 / 青春成长：主题材通常是“末世”，青春成长负责放大关系与失去感

---

## 题材化 `/一键开书` 微模板使用说明

使用通用 `/一键开书` 模板时，再额外补一句：

- 这个题材开篇最先立什么
- 前 3 章最不能丢什么
- 前 10 章反馈重点是什么
- 最容易写崩的点是什么

---

## 题材索引

- 玄幻 / 修仙：`templates/genres/01-xuanhuan-xiuxian.md`
- 都市 / 系统流：`templates/genres/02-dushi-xitongliu.md`
- 种田文：`templates/genres/03-zhongtianwen.md`
- 末世：`templates/genres/04-moshi.md`
- 重生复仇：`templates/genres/06-zhongsheng-fuchou.md`
- 无限流 / 副本流：`templates/genres/07-wuxianliu-fubenliu.md`
- 悬疑 / 刑侦 / 推理：`templates/genres/08-xuanyi-xingzhen-tuili.md`
- 历史 / 权谋：`templates/genres/09-lishi-quanmou.md`
- 轻喜剧 / 沙雕：`templates/genres/10-qingxiju-shadiao.md`
- 直播 / 文娱 / 娱乐圈：`templates/genres/11-zhibo-wenyu-yulequan.md`
- 赛博 / 科幻 / 未来都市：`templates/genres/12-saibo-kehuan-weilaidushi.md`
- 克苏鲁 / 惊悚 / 怪谈：`templates/genres/13-kesulu-jingsong-guaitan.md`
- 校园 / 青春成长：`templates/genres/14-xiaoyuan-qingchun-chengzhang.md`
- 宫斗 / 宅斗：`templates/genres/15-gongdou-zhaidou.md`
- 仙侠恋爱 / 古言甜虐：`templates/genres/16-xianxia-lianai-guyan-tiannue.md`

甜宠 / 情感主导类现言不再单列旧式 Prompt 模板，统一改为：

- 主关系推进：`templates/romance_arc.md`
- 情绪与风格约束：`templates/style-defaults.md`、`templates/style.md`
- 章节落地与避免空转：`references/writing-patterns.md`

---

## 使用建议

- `/一键开书` 时，先看对应题材的“写法重点 + 常见失误”
- `/写` 时，先看对应题材的“推进技巧 + 差例 / 好例”
- 如果题材混合，先确定主题材，再局部借用副题材技巧
- 题材技巧是加成，不替代主技能里的章卡、门禁、记忆更新与节奏控制
