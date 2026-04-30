"""
题材语境词汇漂移检测 — 把 contract 08 的手工规则自动化。

检测维度：
- 古风题材现代词入侵
- 分析腔 / 黑话词检测
- 权谋场抽象词（无事实支撑）
- 军务命令可执行性
- 知识边界（消息提前知情）

独立 CLI 使用：
    python scripts/genre_vocabulary_check.py --project <dir> --chapter <N>
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# 词典定义
# ---------------------------------------------------------------------------

# 古代题材禁止的现代词汇（扩展版 ~200 词）
MODERN_IN_ANCIENT = (
    # 现代组织/制度词
    "公司", "企业", "单位", "部门", "机构", "项目", "方案", "系统",
    "机制", "流程", "绩效", "指标", "考核", "预算", "报销", "审批",
    "会议", "汇报", "报告", "总结", "复盘", "方案", "规划", "策略",
    # 现代分析/管理腔
    "运营", "管理", "优化", "对接", "落地", "赋能", "抓手", "闭环",
    "底层逻辑", "顶层设计", "核心资产", "资源整合", "有效触达",
    # 现代社交/关系词
    "社交", "人脉", "资源", "变现", "情绪价值", "心理建设",
    # 现代心理/分析词
    "心理", "心理学", "情绪管理", "共情", "边界感", "安全感",
    "原生家庭", "童年阴影", "潜意", "投射",
    # 现代科技/信息词
    "信息", "数据", "信号", "频道", "频率", "雷达", "定位",
    # 现代政治/社会词
    "民主", "自由", "平等", "人权", "法治", "宪法",
    # 现代计量/金融词
    "利率", "汇率", "GDP", "通胀", "杠杆", "流动性",
)

# 分析腔 / 黑话词（题材无关，网文通用禁忌）
ANALYSIS_JARGON = (
    "拉扯", "博弈", "信息差", "压迫感", "站队", "绑定", "情绪价值",
    "张力", "分寸", "体面", "名分", "太满", "太薄", "太冷", "太热",
    "压住", "稳住", "风口", "挨刀", "棋子", "刀鞘", "弃子",
    "入局", "破局", "承局", "站位", "态度", "牵制", "拉进来",
    "站到身后", "看重",
)

# 权谋/军政抽象词（必须伴随具体事实，否则标记）
ABSTRACT_POLITICS = (
    "局势", "局面", "处境", "代价", "后果",
    "位置", "态度", "分寸", "体面",
)

# 作者总结腔
AUTHORIAL_SUMMARY_PATTERNS = (
    "不是……而是", "真正要命的是", "真正的问题是", "这不是",
    "这才是", "无非是", "终究是", "从来都是", "像极了",
    "说到底", "本质上", "某种意义上", "毫无疑问", "这意味着",
    "这说明", "说白了", "说穿了", "归根到底", "关键在于",
)

# 模糊/规避表达（滥用"那个人/那件事"）
VAGUE_REFERENCES = (
    "那个人", "那件事", "那个地方", "某种真相", "某个答案",
    "说不清", "难以言明", "不可名状", "没有说破", "没有点破",
)

# 军务命令标记 — 下命令后必须跟执行信息
ORDER_MARKERS = (
    "传令", "下令", "军令", "听令", "号令", "速去", "立刻",
    "马上", "调", "撤", "守", "封", "补", "点火", "杀",
)

# 命令执行要素（执行者 / 行动 / 后果各一即可）
ORDER_EXECUTION_WHO = (
    "你", "我", "他和", "带", "领", "率", "遣", "派",
    "亲兵", "卫队", "哨骑", "游骑", "前屏", "白甲",
    "何川", "马承", "沈", "赵", "李", "王", "张", "刘",
)
ORDER_EXECUTION_DO = (
    "去", "带人", "带上", "把", "拿", "守住", "看住", "盯着",
    "查", "问", "审", "烧", "拆", "填", "堵", "开", "关",
    "围", "追", "截", "拦", "接应", "掩护",
)
ORDER_CONSEQUENCE = (
    "不然", "否则", "再拖", "慢一步", "就会", "就要", "会让",
    "会把", "就得", "守不住", "失守", "断粮", "散掉",
    "摸上来", "空出来", "顶不住", "来不及", "过了夜",
)

# 知识泄露标记 — 应该不知道的事提前知道
KNOWLEDGE_LEAK_MARKERS = (
    "已经知道", "早就知道", "听说", "得到消息", "接到信",
    "消息传到", "探子回报", "暗哨传回",
)


def _char_count(text: str) -> int:
    """计算中文字符数。"""
    return sum(1 for c in text if "\u4e00" <= c <= "\u9fff")


def _has_explanation_for_politics(text: str, keyword: str, window: int = 80) -> bool:
    """检查抽象词附近是否有具体事实（人名/数量/地点/动作）。"""
    idx = text.find(keyword)
    if idx < 0:
        return True  # 不是这个触发点
    start = max(0, idx - window)
    end = min(len(text), idx + window)
    context = text[start:end]
    # 有具体数字（人数、时间、数量）
    if re.search(r"\d+", context):
        return True
    # 有具体地点
    if re.search(r"(驿|城|关|楼|营|府|宫|殿|门|墙|巷|街|道|坡|岭)", context):
        return True
    # 有具体人名出现在附近
    if re.search(r"(何川|马承|沈|赵|李|王|张|刘)", context):
        return True
    # 有具体动作
    if re.search(r"(伸手|抬脚|转身|推门|按|抓|握住|端起|放下)", context):
        return True
    return False


# ---------------------------------------------------------------------------
# 检测函数
# ---------------------------------------------------------------------------

def _check_modern_in_ancient(text: str) -> list[dict]:
    """古代题材现代词入侵检测。"""
    issues: list[dict] = []
    chinese_chars = _char_count(text)
    if chinese_chars == 0:
        return issues

    found: list[dict] = []
    for word in MODERN_IN_ANCIENT:
        count = text.count(word)
        if count > 0:
            # 定位首处出现位置
            idx = text.find(word)
            context_start = max(0, idx - 10)
            context_end = min(len(text), idx + len(word) + 10)
            context = text[context_start:context_end].replace("\n", " ")
            found.append({"word": word, "count": count, "context": f"...{context}..."})

    if found:
        word_list = ", ".join(f'"{w["word"]}"({w["count"]}次)' for w in found[:10])
        issues.append({
            "type": "modern_in_ancient",
            "severity": "high",
            "reason": f"古代题材正文出现现代词汇: {word_list}",
            "details": found[:10],
        })

    return issues


def _check_analysis_jargon(text: str) -> list[dict]:
    """分析腔/黑话词检测。"""
    issues: list[dict] = []
    chinese_chars = _char_count(text)
    if chinese_chars == 0:
        return issues

    found: list[dict] = []
    for word in ANALYSIS_JARGON:
        count = text.count(word)
        if count > 0:
            idx = text.find(word)
            context_start = max(0, idx - 10)
            context_end = min(len(text), idx + len(word) + 10)
            context = text[context_start:context_end].replace("\n", " ")
            found.append({"word": word, "count": count, "context": f"...{context}..."})

    if found:
        word_list = ", ".join(f'"{w["word"]}"({w["count"]}次)' for w in found[:8])
        issues.append({
            "type": "analysis_jargon",
            "severity": "high",
            "reason": f"正文出现分析腔/黑话词: {word_list}。应替换为具体动作、座次、视线、军令、账册、后果",
            "details": found[:8],
        })

    return issues


def _check_abstract_politics(text: str) -> list[dict]:
    """权谋/军政抽象词检测（无事实支撑）。"""
    issues: list[dict] = []

    for word in ABSTRACT_POLITICS:
        count = text.count(word)
        if count > 0 and not _has_explanation_for_politics(text, word):
            idx = text.find(word)
            context_start = max(0, idx - 15)
            context_end = min(len(text), idx + len(word) + 15)
            context = text[context_start:context_end].replace("\n", " ")
            issues.append({
                "type": "abstract_politics_unsupported",
                "severity": "high",
                "reason": f"抽象词'{word}'附近缺少具体事实支撑（人数/地点/动作/后果）。"
                           f"上下文: ...{context}...",
            })

    return issues


def _check_orders_executable(text: str) -> list[dict]:
    """军务命令可执行性检测。"""
    issues: list[dict] = []
    sentences = re.split(r"[。！？]", text)

    for i, sent in enumerate(sentences):
        if not any(marker in sent for marker in ORDER_MARKERS):
            continue
        # 找到命令句后 1-3 句
        follow_up = sentences[i:min(i + 4, len(sentences))]
        follow_text = "。".join(follow_up)

        has_who = any(marker in follow_text for marker in ORDER_EXECUTION_WHO)
        has_do = any(marker in follow_text for marker in ORDER_EXECUTION_DO)
        has_consequence = any(marker in follow_text for marker in ORDER_CONSEQUENCE)

        # 需要至少 2/3
        score = sum([has_who, has_do, has_consequence])
        if score < 2:
            missing = []
            if not has_who:
                missing.append("执行者")
            if not has_do:
                missing.append("具体行动")
            if not has_consequence:
                missing.append("后果/紧急性")
            issues.append({
                "type": "unexecutable_order",
                "severity": "high",
                "reason": f"命令句'{sent.strip()[:30]}...'缺少{', '.join(missing)}，"
                           f"后文未充分交代谁去做、先做什么、慢一步会怎样",
            })

    return issues


def _check_authorial_summary(text: str) -> list[dict]:
    """作者总结腔检测。"""
    issues: list[dict] = []

    # 检测固定模式
    for pattern in ("不是", "这才是", "真正要命的是", "说到底", "本质上",
                     "某种意义上", "毫无疑问", "说白了", "说穿了"):
        count = text.count(pattern)
        if count > 0:
            idx = text.find(pattern)
            context_start = max(0, idx - 10)
            context_end = min(len(text), idx + len(pattern) + 20)
            context = text[context_start:context_end].replace("\n", " ")
            issues.append({
                "type": "authorial_summary",
                "severity": "high",
                "reason": f"作者总结腔: '...{context}...'。应替换为角色动作或现场反应",
                "pattern": pattern,
            })

    # 检测"这意味着/这说明"
    for phrase in ("这意味着", "这说明", "也就是说", "换句话说"):
        count = text.count(phrase)
        if count > 0:
            issues.append({
                "type": "authorial_explanation",
                "severity": "medium",
                "reason": f"作者解释腔'{phrase}'出现 {count} 次。读者不需要作者替他们做阅读理解",
            })

    return issues


def _check_vague_references(text: str) -> list[dict]:
    """模糊/规避表达检测。"""
    issues: list[dict] = []

    count_map: dict[str, int] = {}
    for phrase in VAGUE_REFERENCES:
        c = text.count(phrase)
        if c > 0:
            count_map[phrase] = c

    if count_map:
        total = sum(count_map.values())
        details = ", ".join(f'"{k}"({v}次)' for k, v in count_map.items())
        issues.append({
            "type": "vague_reference_overuse",
            "severity": "medium",
            "reason": f"模糊/规避表达出现 {total} 次: {details}。"
                       f"普通信息绕写成'那个人/那件事'会削弱信息密度",
        })

    return issues


def _check_knowledge_boundary(text: str, chapter_cards: list[dict] | None = None) -> list[dict]:
    """知识边界检测（基础版）。"""
    issues: list[dict] = []

    # 检测同时出现"消息还没到"与"已经知道"的矛盾
    has_not_arrived = bool(re.search(r"(还没到|未送达|还没传|还没接到|尚未接到)", text))
    has_already_known = bool(re.search(r"(已经知道|早就知道|早已知道|已然知道)", text))

    if has_not_arrived and has_already_known:
        issues.append({
            "type": "knowledge_timing_contradiction",
            "severity": "high",
            "reason": "正文同时出现'消息未到'和'已经知道'，存在知识边界前后矛盾",
        })

    return issues


# ---------------------------------------------------------------------------
# 主审计函数
# ---------------------------------------------------------------------------

def analyze_genre_vocabulary(
    text: str,
    *,
    genre: str = "ancient",
    chapter_cards: list[dict] | None = None,
    silence: bool = False,
) -> dict:
    """
    题材语境词汇漂移审计。

    Args:
        text: 章节正文
        genre: 题材类型 ("ancient" | "modern" | "xianxia" | "scifi")
        chapter_cards: 章卡列表（可选，用于知识边界跨章检测）
        silence: 是否抑制输出

    Returns:
        { "verdict": "pass"|"warn"|"rewrite", "issues": [...], "scores": {...} }
    """
    all_issues: list[dict] = []

    # 古风题材特定检查
    if genre == "ancient":
        all_issues.extend(_check_modern_in_ancient(text))

    # 通用于所有题材
    all_issues.extend(_check_analysis_jargon(text))
    all_issues.extend(_check_abstract_politics(text))
    all_issues.extend(_check_orders_executable(text))
    all_issues.extend(_check_authorial_summary(text))
    all_issues.extend(_check_vague_references(text))
    all_issues.extend(_check_knowledge_boundary(text, chapter_cards))

    # 综合裁决
    high_count = sum(1 for i in all_issues if i["severity"] == "high")
    medium_count = sum(1 for i in all_issues if i["severity"] == "medium")

    if high_count >= 3:
        verdict = "rewrite"
    elif high_count >= 1 or medium_count >= 5:
        verdict = "warn"
    else:
        verdict = "pass"

    result = {
        "verdict": verdict,
        "genre": genre,
        "issues": all_issues,
        "issue_count": len(all_issues),
        "high_issue_count": high_count,
        "medium_issue_count": medium_count,
        "scores": {
            "genre_purity": max(0, 100 - high_count * 20 - medium_count * 5),
        },
    }

    if not silence:
        print(f"题材词汇审计 [{genre}] — 发现 {len(all_issues)} 个问题"
              f"（高 {high_count} / 中 {medium_count}）→ {verdict}")
        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['reason'][:120]}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_chapter_path(project_dir: Path, chapter: int) -> Path:
    candidates = [
        project_dir / "02_chapters" / f"ch{chapter:03d}.md",
        project_dir / "02_first_draft" / f"ch{chapter:03d}.md",
        project_dir / "02_first_draft" / f"ch{chapter}.md",
    ]
    draft_dir = project_dir / "02_first_draft"
    if draft_dir.exists():
        for f in sorted(draft_dir.glob(f"ch{chapter:03d}*.md")):
            candidates.append(f)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"找不到第 {chapter} 章的正文文件")


def _detect_genre_from_plan(project_dir: Path) -> str:
    """从 plan.md/schema 推断题材。"""
    plan_path = project_dir / "00_memory" / "plan.md"
    schema_path = project_dir / "00_memory" / "schema" / "plan.json"

    if schema_path.exists():
        try:
            data = json.loads(schema_path.read_text(encoding="utf-8"))
            genre = str(data.get("genre", "")).strip()
            if genre:
                return genre
        except (json.JSONDecodeError, KeyError):
            pass

    if plan_path.exists():
        content = plan_path.read_text(encoding="utf-8")
        ancient_keywords = ("古代", "历史", "权谋", "军政", "宫斗", "穿越", "重生古")
        modern_keywords = ("现代", "都市", "校园", "职场", "娱乐圈", "总裁")
        xianxia_keywords = ("修仙", "玄幻", "仙侠", "修真", "洪荒", "神话")

        for kw in ancient_keywords:
            if kw in content:
                return "ancient"
        for kw in modern_keywords:
            if kw in content:
                return "modern"
        for kw in xianxia_keywords:
            if kw in content:
                return "xianxia"

    return "ancient"  # 默认古代


def main() -> None:
    parser = argparse.ArgumentParser(description="题材语境词汇漂移检测")
    parser.add_argument("--project", type=str, required=True, help="项目根目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--genre", type=str, default=None,
                        help="题材类型 (ancient|modern|xianxia|scifi)，默认从 plan 推断")
    parser.add_argument("--text", type=str, default=None, help="直接传入文本")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"项目目录不存在: {project_dir}")
        return

    genre = args.genre or _detect_genre_from_plan(project_dir)

    if args.text:
        text = args.text
    else:
        chapter_path = _resolve_chapter_path(project_dir, args.chapter)
        text = chapter_path.read_text(encoding="utf-8")

    result = analyze_genre_vocabulary(text, genre=genre)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
