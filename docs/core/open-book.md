# 开书主链路

> 这是重构后的核心开书入口文档。Phase 1 先建立主入口，不改变旧命令兼容层。

## 适用场景
- 新开一本中文网文长篇连载
- 重做题材定位、卖点、黄金三章、卷纲、阶段目标
- 发现开篇抓不住人、前三章散、长期承诺不清

## 开书优先级
1. 读者为什么现在继续看
2. 第一卷到底在打什么
3. 主角缺什么、怕什么、靠什么改命
4. 黄金三章各自承担什么功能
5. 这本书怎么说话，而不是只会一个平台腔

## 中文网文默认优先级
如果用户没有额外指定平台策略，默认按这个顺序取舍：

1. 读者想不想继续看
2. 这一章 / 这一段有没有功能
3. 爽点、情绪点、悬念点是否落地
4. 人物有没有继续向前走
5. 设定是否稳定
6. 文字是否顺滑

这意味着：
- 单章文采不能代替推进
- 信息量不能代替冲突
- 热闹不能代替主线
- 设定堆砌不能代替剧情兑现
- 默认先说人话，先让读者看懂人在干什么、为什么这么干、结果变了什么

## 最小开书流程
1. 先定题材与主卖点
2. 再定主冲突、阶段目标、卷级推进
3. 再定黄金三章功能链
4. 再补角色结构、关系压力、资源状态
5. 最后再补书级 `style.md` / `voice.md`

## 开篇常见错误
- 设定讲太多，冲突来太晚
- 主角没有明确欲望，只是在被剧情推着走
- 爽点承诺不清，读者不知道这本书到底卖什么
- 三章过去仍没有明显推进
- 所有信息都在解释，没有场景结果
- 卖点、简介、正文都在说虚话，看完还是不知道主角到底要干什么

## 开书必产物
- `00_memory/plan.md`
- `00_memory/state.md`
- `00_memory/style.md`
- `00_memory/voice.md`
- 卷纲 / 阶段目标
- 黄金三章路线

## 推荐搭配
- 开书总入口：`templates/launch/opening-kit.md`
- 卷纲：`templates/launch/volume-blueprint.md`
- 世界与设定：`templates/launch/worldbuilding-kit.md`
- 题材包：`docs/assets/genre-index.md`
- 单书风格锚点：`templates/core/style.md`
- 书级声音：`templates/core/voice.md`

## 迁移说明
当前阶段：
- 旧资料仍作为兼容层保留
- 新主入口优先集中到 `docs/core/*`、`docs/assets/*` 与 `templates/launch/*`

当前已经可用的新入口：
- `chase open --project <dir>`
- `chase open --project <dir> --chapter <n>`

行为：
- 不带 `--chapter`：做开书 readiness 扫描，检查 `plan.md / state.md / style.md / voice.md / characters.md`
- 带 `--chapter`：兼容走章节规划与上下文准备
