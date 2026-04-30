# opening：开书与开写前准备

`opening` 是 `chaseNovel` 第一批优先成形的子 skill 之一。

它负责两类事情：
1. **book opening**：把一本书开起来
2. **chapter opening**：在已有项目上，为下一章做 planning/context readiness

它不是正文生成主链，也不替 `writer` 写正文。

## 适用场景
- 新开一本中文网文长篇连载
- 重做题材定位、卖点、黄金三章、卷纲、阶段目标
- 发现开篇抓不住人、前三章散、长期承诺不清
- 写某一章前，需要先准备下一章的 planning/context

## `opening` 负责什么

### book opening
- 题材定位
- 受众卖点
- 一句话卖点
- 主角驱动力与主线目标
- 黄金三章
- 卷纲 / 阶段目标
- 开篇承诺
- 初始化记忆文件建议

### chapter opening
- 基于当前 `reference_chapter` 恢复下一章 planning 前提
- 产出 `target_chapter` 的 readiness
- 明确下一章最该推进什么
- 明确下一章不能丢什么承诺 / 后果 / 钩子

## 开书优先级
1. 读者为什么现在继续看
2. 第一卷到底在打什么
3. 主角缺什么、怕什么、靠什么改命
4. 黄金三章各自承担什么功能
5. 这本书怎么说话，而不是只会一个平台腔

## 中文网文默认优先级
如果没有额外平台策略，默认按这个顺序取舍：

1. 读者想不想继续看
2. 这一章 / 这一段有没有功能
3. 爽点、情绪点、悬念点是否落地
4. 人物有没有继续往前走
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
5. 最后补书级 `style.md` / `voice.md`

## 开篇常见错误
- 设定讲太多，冲突来太晚
- 主角没有明确欲望，只是在被剧情推着走
- 卖点承诺不清，读者不知道这本书到底卖什么
- 三章过去仍没有明显推进
- 所有信息都在解释，没有场景结果
- 卖点、简介、正文都在说虚话，看完仍不知道主角到底要干什么

## `opening` 必产物
- `00_memory/plan.md`
- `00_memory/state.md`
- `00_memory/style.md`
- `00_memory/voice.md`
- 卷纲 / 阶段目标
- 黄金三章路线
- chapter opening 时的下一章 planning/context 结论

## 推荐搭配
- 开书总入口：`templates/launch/opening-kit.md`
- 卷纲：`templates/launch/volume-blueprint.md`
- 世界与设定：`templates/launch/worldbuilding-kit.md`
- 长线计划：`templates/core/plan.md`
- 题材包：`docs/assets/genre-index.md`
- 单书风格锚点：`templates/core/style.md`
- 书级声音：`templates/core/voice.md`

## 当前 shipped CLI 入口
- `chase open --project <dir>`
- `chase open --project <dir> --chapter <current-drafted-n>`
- `chase open --project <dir> --chapter <current-drafted-n> --target-chapter <target-n>`

当前 owner 关系：
- `open_book.py` 是唯一公开的 `open` 入口
- `open_book.py` 内部直接聚合 next-chapter readiness
- `write / check` 中的 `open` 步骤也应保持这层 owner 关系

## 章节语义
- 不带章节参数：做 **book opening / launch readiness** 扫描
- 带 `--chapter <n>`：把它视为当前已写的 `reference_chapter`
- 默认准备下一章，即 `target_chapter = n + 1`
- 带 `--target-chapter`：显式指定要准备的目标章节

## 与 `write` / `check` 的关系
- `opening` 负责开书与开写前准备
- `writer` 负责正文生成
- `open` 只负责下一章 `target_chapter` 的 planning/context 预审
- `write` 默认链路是 `open,runtime,quality,status`
- `check` 默认链路是 `open,quality,status`
- `check` 会复用 `open` 的预审结果，但不会进入 `runtime`
- 当前章节的质量放行由 `quality` 负责，不由 `opening` 负责

## 边界说明
- `opening` 不负责直接写正文
- `opening` 不负责改章诊断
- `opening` 不负责独立风格精修
- `opening` 可以给 `writer`、`continue` 提供 planning/context 前提，但不替它们执行正文与修稿链
