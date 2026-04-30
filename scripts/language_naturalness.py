"""
中文自然度分析模块 — 超越关键词检测的结构性语言质感分析。

与 language_audit.py 互补：audit 查违规（是否写了不该写的），
naturalness 查质感（读起来是否像人写的）。

独立 CLI 使用：
    python scripts/language_naturalness.py --project <dir> --chapter <N>
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 句长节奏：熵阈值
SENTENCE_RHYTHM_ENTROPY_LOW = 1.5          # 熵 < 1.5 → 节奏单调

# 句首多样性：连续句首 2-gram 重复率阈值
SENTENCE_OPENING_REPEAT_THRESHOLD = 0.30   # >30% → 句式单一

# 过渡词密度（每千字）
TRANSITION_PER_1000_THRESHOLD = 8          # >8‰ → 流水账感

# 视觉节拍覆盖度
VISUAL_BEAT_MIN_RATIO = 0.15               # <15% → 抽象过重

# 内心独白占比
INNER_MONOLOGUE_MAX_RATIO = 0.20           # >20% → 内心戏过重

# 对话主动性
DIALOGUE_INITIATIVE_MIN_RATIO = 0.30       # <30% → 主角被动

# "了"字密度（每千字）
LE_PER_1000_THRESHOLD = 35                 # >35‰ → 语气助词泛滥

# 成语密度：单段内堆积
IDIOM_PER_PARAGRAPH_THRESHOLD = 3          # 单段 >3 → 堆砌感

# 展示/告知比
SHOW_TELL_MIN_RATIO = 1.0                  # <1.0 → 告知过重


# 中文句子结束标记
_SENTENCE_END_RE = re.compile(r"[。！？…；\n]")

# 中文分句（以句号、问号、感叹号、分号断句）
_CLAUSE_SPLIT_RE = re.compile(r"[。！？；]+")

# 过渡词
_TRANSITION_WORDS = ("然后", "接着", "于是", "便", "随即", "随后", "紧接着", "接下来")

# 视觉/感官细节词
_VISUAL_SENSORY_WORDS = (
    # 视觉
    "看见", "看到", "望见", "映入", "眼前", "远处", "近处",
    # 听觉
    "听见", "听到", "声", "响", "静", "嗡", "砰", "咔", "啪",
    # 触觉
    "冰凉", "烫", "冷", "热", "硬", "软", "粗糙", "光滑", "汗",
    # 动作（具体可观察的）
    "伸手", "抬脚", "转身", "推", "拉", "扯", "按", "抓", "握", "攥",
    "站起身", "坐下", "跪下", "起身", "低头", "抬眼", "扭头", "侧身",
    "端起", "放下", "递", "接", "扔", "抛", "砸", "踢", "踹",
    # 嗅觉
    "闻到", "气味", "腥", "臭", "香",
)

# 内心独白标记（思维动词）
_INNER_MONOLOGUE_MARKERS = (
    "觉得", "想", "知道", "明白", "意识到", "感到", "感觉", "以为",
    "认为", "记得", "忘记", "怀疑", "确定", "肯定", "猜测",
)

# 抽象判断词（用于 show/tell 比计算的 "tell" 侧）
_ABSTRACT_JUDGMENT_WORDS = (
    "局势", "局面", "处境", "代价", "后果", "压力", "风险", "选择",
    "问题", "本质", "真相", "结果", "变化", "推进", "命运", "宿命",
    "压迫感", "拉扯", "博弈", "信息差", "张力", "情绪价值", "绑定",
    "站队", "分寸", "体面", "名分", "太满", "太薄", "太冷", "太热",
    "压住", "稳住", "风口", "挨刀", "棋子", "刀鞘", "弃子",
)

# 成语列表（内置 200+ 常用成语）
_COMMON_IDIOMS = frozenset({
    "心知肚明", "不动声色", "若无其事", "胸有成竹", "泰然自若",
    "面不改色", "目不转睛", "耳聪目明", "心领神会", "心照不宣",
    "不言而喻", "显而易见", "昭然若揭", "一目了然", "一览无余",
    "众所周知", "家喻户晓", "尽人皆知", "无人不晓", "妇孺皆知",
    "溢于言表", "难以言表", "不可言喻", "不言自明", "心有余悸",
    "如坐针毡", "如履薄冰", "如临深渊", "如临大敌", "如芒在背",
    "胆战心惊", "心惊肉跳", "心慌意乱", "六神无主", "魂不守舍",
    "失魂落魄", "魂飞魄散", "毛骨悚然", "不寒而栗", "战战兢兢",
    "小心翼翼", "谨小慎微", "步步为营", "稳扎稳打", "循规蹈矩",
    "按部就班", "中规中矩", "墨守成规", "一成不变", "一如既往",
    "千篇一律", "雷打不动", "始终如一", "一如既往", "日复一日",
    "年复一年", "周而复始", "循环往复", "往复循环", "来日方长",
    "长此以往", "久而久之", "旷日持久", "遥遥无期", "指日可待",
    "势在必行", "箭在弦上", "迫在眉睫", "燃眉之急", "当务之急",
    "刻不容缓", "时不我待", "机不可失", "失不再来", "稍纵即逝",
    "进退两难", "左右为难", "骑虎难下", "进退维谷", "腹背受敌",
    "内外交困", "四面楚歌", "穷途末路", "山穷水尽", "走投无路",
    "死路一条", "绝处逢生", "起死回生", "转危为安", "化险为夷",
    "峰回路转", "柳暗花明", "绝地反击", "翻盘逆转", "力挽狂澜",
    "风云变幻", "变幻莫测", "波谲云诡", "暗流涌动", "风起云涌",
    "山雨欲来", "黑云压城", "一触即发", "剑拔弩张", "千钧一发",
    "气定神闲", "镇定自若", "不动如山", "稳如泰山", "处变不惊",
    "临危不惧", "无所畏惧", "义无反顾", "勇往直前", "一往无前",
    "势如破竹", "锐不可当", "所向披靡", "攻无不克", "战无不胜",
    "无坚不摧", "无往不利", "势不可挡", "摧枯拉朽", "排山倒海",
    "天翻地覆", "翻天覆地", "沧海桑田", "物是人非", "时过境迁",
    "斗转星移", "光阴似箭", "日月如梭", "白驹过隙", "弹指一挥",
    "转瞬即逝", "瞬息万变", "千变万化", "瞬息之间", "电光石火",
})

# 主角名识别标记（将第 2-4 字非普通角色名字符视为主角候选）
_PROTAGONIST_NAME_PATTERN = re.compile(r"([\u4e00-\u9fff]{2,4})")


# ---------------------------------------------------------------------------
# 核心分析函数
# ---------------------------------------------------------------------------

def _extract_sentences(text: str) -> list[str]:
    """以中文标点分句，返回非空句子列表。"""
    parts = _CLAUSE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def _extract_paragraphs(text: str) -> list[str]:
    """按空行分段，返回非空段落列表。"""
    paragraphs = []
    current: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append("".join(current))
                current = []
        else:
            current.append(stripped)
    if current:
        paragraphs.append("".join(current))
    return paragraphs


def _extract_dialogue_lines(text: str) -> list[str]:
    """提取中文双引号内对白内容。"""
    pattern = re.compile(r'["\u201c]([^"\u201d\n]{2,120})["\u201d]')
    return [m.group(1).strip() for m in pattern.finditer(text)]


def _extract_dialogue_with_speaker(text: str) -> list[tuple[str, str]]:
    """提取对白及说话人。返回 [(说话人, 对白内容), ...]。
    说话人从引号前 15 字内匹配角色名（中文 2-4 字）。
    """
    pattern = re.compile(r'([\u4e00-\u9fff]{2,4})[^"\u201c\n]{0,15}["\u201c]([^"\u201d]{2,120})["\u201d]')
    results: list[tuple[str, str]] = []
    for m in pattern.finditer(text):
        speaker = m.group(1).strip()
        content = m.group(2).strip()
        results.append((speaker, content))
    return results


def _char_count(text: str) -> int:
    """计算中文字符数（去除空白和标点）。"""
    return sum(1 for c in text if "\u4e00" <= c <= "\u9fff")


def _count_in_text(text: str, keywords: tuple[str, ...]) -> int:
    """统计关键词在文本中出现的总次数（不重叠）。"""
    total = 0
    for kw in keywords:
        total += text.count(kw)
    return total


# ---------------------------------------------------------------------------
# 检测维度
# ---------------------------------------------------------------------------

def _check_sentence_rhythm(sentences: list[str]) -> dict:
    """句长节奏熵检测。"""
    if len(sentences) < 5:
        return {"score": 100, "entropy": None, "issues": []}

    lengths = [len(s) for s in sentences]
    total = sum(lengths)
    if total == 0:
        return {"score": 100, "entropy": None, "issues": []}

    # 按长度分桶
    buckets: dict[str, int] = {"short(≤10)": 0, "mid(11-22)": 0, "long(23-40)": 0, "very_long(>40)": 0}
    for le in lengths:
        if le <= 10:
            buckets["short(≤10)"] += 1
        elif le <= 22:
            buckets["mid(11-22)"] += 1
        elif le <= 40:
            buckets["long(23-40)"] += 1
        else:
            buckets["very_long(>40)"] += 1

    n = len(sentences)
    entropy = -sum(
        (count / n) * math.log2(max(count / n, 1e-9))
        for count in buckets.values()
        if count > 0
    )

    issues: list[dict] = []
    if entropy < SENTENCE_RHYTHM_ENTROPY_LOW:
        # 找出占比最高的桶
        max_bucket = max(buckets.items(), key=lambda x: x[1])
        issues.append({
            "type": "sentence_rhythm_monotone",
            "severity": "medium",
            "reason": f"句长节奏熵={entropy:.2f}（<{SENTENCE_RHYTHM_ENTROPY_LOW}），"
                       f"'{max_bucket[0]}' 占比 {max_bucket[1]}/{n}，节奏缺乏变化",
        })

    score = max(0, min(100, int(entropy / 2.0 * 100)))
    return {"score": score, "entropy": round(entropy, 2), "distribution": buckets, "issues": issues}


def _check_sentence_openings(sentences: list[str]) -> dict:
    """句首多样性检测。"""
    if len(sentences) < 8:
        return {"score": 100, "issues": []}

    # 取每句首 2 字作为 opening bigram
    openings = [s[:2] if len(s) >= 2 else s for s in sentences]
    counter = Counter(openings)
    total = len(openings)
    repeat_count = sum(max(0, c - 1) for c in counter.values())
    repeat_ratio = repeat_count / total if total > 0 else 0

    issues: list[dict] = []
    if repeat_ratio > SENTENCE_OPENING_REPEAT_THRESHOLD:
        top_repeats = counter.most_common(3)
        issues.append({
            "type": "sentence_opening_monotone",
            "severity": "medium",
            "reason": f"句首 2-gram 重复率={repeat_ratio:.1%}（>{SENTENCE_OPENING_REPEAT_THRESHOLD:.0%}），"
                       f"最常见句首: {', '.join(f'{k}({v}次)' for k, v in top_repeats)}",
        })

    score = max(0, min(100, int((1 - repeat_ratio) * 100)))
    return {"score": score, "repeat_ratio": round(repeat_ratio, 3), "issues": issues}


def _check_paragraph_pattern(paragraphs: list[str]) -> dict:
    """段落结构重复检测 — 连续 3 段是否同一结构模式。"""
    issues: list[dict] = []

    if len(paragraphs) < 3:
        return {"score": 100, "issues": []}

    def _classify_paragraph(text: str) -> str:
        """简单分类：描写 / 心理 / 动作 / 对话 / 混合。"""
        chinese_chars = _char_count(text)
        if chinese_chars == 0:
            return "empty"

        dialogue_pattern = re.compile(r'["\u201c]')
        dialogue_count = len(dialogue_pattern.findall(text))
        if dialogue_count > chinese_chars * 0.1:
            return "dialogue"

        action_count = _count_in_text(text, (
            "伸手", "抬脚", "转身", "推", "拉", "扯", "按", "抓", "握", "攥",
            "站起身", "坐下", "跪下", "低头", "抬眼", "扭头", "端起", "放下",
        ))
        inner_count = _count_in_text(text, _INNER_MONOLOGUE_MARKERS)
        desc_count = _count_in_text(text, ("的", "了", "在", "是", "有", "着"))

        if inner_count > desc_count * 0.2:
            return "inner"
        if action_count > 2:
            return "action"
        if desc_count > chinese_chars * 0.05:
            return "description"
        return "mixed"

    patterns: list[str] = []
    streak_start = 0
    for i, p_text in enumerate(paragraphs):
        p_type = _classify_paragraph(p_text)
        patterns.append(p_type)

        if i >= 2:
            if patterns[i] == patterns[i - 1] == patterns[i - 2]:
                if i - streak_start >= 2:
                    issues.append({
                        "type": "paragraph_pattern_repeat",
                        "severity": "medium",
                        "reason": f"第 {streak_start + 1}-{i + 1} 段连续 {i - streak_start + 1} 段"
                                  f"为同一结构模式'{p_type}'，段落节奏机械",
                    })
                streak_start = i - 2
            else:
                streak_start = i - 1

    score = max(0, min(100, 100 - len(issues) * 10))
    return {"score": score, "patterns": patterns, "issues": issues}


def _check_transition_overuse(text: str) -> dict:
    """过渡词密度检测。"""
    chinese_chars = _char_count(text)
    if chinese_chars == 0:
        return {"score": 100, "issues": []}

    total_count = _count_in_text(text, _TRANSITION_WORDS)
    density_per_1000 = (total_count / chinese_chars) * 1000

    issues: list[dict] = []
    if density_per_1000 > TRANSITION_PER_1000_THRESHOLD:
        # 统计每个过渡词的频次
        detail = {w: text.count(w) for w in _TRANSITION_WORDS if text.count(w) > 0}
        issues.append({
            "type": "transition_overuse",
            "severity": "medium",
            "reason": f"过渡词密度={density_per_1000:.1f}‰（>{TRANSITION_PER_1000_THRESHOLD}‰），"
                       f"分布: {detail}",
        })

    score = max(0, min(100, int(100 - density_per_1000 * 5)))
    return {"score": score, "density_per_1000": round(density_per_1000, 1), "details": {
        w: text.count(w) for w in _TRANSITION_WORDS if text.count(w) > 0
    }, "issues": issues}


def _check_visual_beat_coverage(sentences: list[str]) -> dict:
    """视觉节拍覆盖度检测。"""
    if len(sentences) < 5:
        return {"score": 100, "issues": []}

    nailed_count = sum(
        1 for s in sentences
        if any(kw in s for kw in _VISUAL_SENSORY_WORDS)
    )
    total = len(sentences)
    ratio = nailed_count / total

    issues: list[dict] = []
    if ratio < VISUAL_BEAT_MIN_RATIO:
        issues.append({
            "type": "visual_beat_insufficient",
            "severity": "medium",
            "reason": f"含感官细节句子占比={ratio:.1%}（<{VISUAL_BEAT_MIN_RATIO:.0%}），"
                       f"文本偏重抽象叙述，缺少可感知的具体动作/画面",
        })

    score = max(0, min(100, int(ratio / VISUAL_BEAT_MIN_RATIO * 60)))
    return {"score": score, "ratio": round(ratio, 3), "issues": issues}


def _check_inner_monologue_ratio(sentences: list[str]) -> dict:
    """内心独白占比检测。"""
    if len(sentences) < 5:
        return {"score": 100, "issues": []}

    inner_count = sum(
        1 for s in sentences
        if any(kw in s for kw in _INNER_MONOLOGUE_MARKERS)
    )
    total = len(sentences)
    ratio = inner_count / total

    issues: list[dict] = []
    if ratio > INNER_MONOLOGUE_MAX_RATIO:
        issues.append({
            "type": "inner_monologue_excessive",
            "severity": "medium",
            "reason": f"内心独白句占比={ratio:.1%}（>{INNER_MONOLOGUE_MAX_RATIO:.0%}），"
                       f"内心戏过重，读者被锁在主角头脑里出不去",
        })

    score = max(0, min(100, int((1 - ratio / 0.4) * 100)))
    return {"score": score, "ratio": round(ratio, 3), "issues": issues}


def _check_dialogue_initiative(text: str, protagonist_name: str) -> dict:
    """对话主动性检测 — 主角是否主动发起对话。"""
    dialogue_pairs = _extract_dialogue_with_speaker(text)
    if len(dialogue_pairs) < 3:
        return {"score": 100, "issues": []}

    # 找到说话人切换点：A 说完 → B 说。A 是发起方
    initiative_count = 0
    total_switch = 0
    for i in range(1, len(dialogue_pairs)):
        prev_speaker = dialogue_pairs[i - 1][0]
        curr_speaker = dialogue_pairs[i][0]
        if prev_speaker != curr_speaker:
            total_switch += 1
            if prev_speaker == protagonist_name:
                initiative_count += 1

    if total_switch == 0:
        return {"score": 100, "issues": []}

    ratio = initiative_count / total_switch

    issues: list[dict] = []
    if ratio < DIALOGUE_INITIATIVE_MIN_RATIO and protagonist_name:
        issues.append({
            "type": "protagonist_passive_dialogue",
            "severity": "medium",
            "reason": f"主角'{protagonist_name}'主动发起对话占比={ratio:.1%}（<{DIALOGUE_INITIATIVE_MIN_RATIO:.0%}），"
                       f"主角在对话中偏被动反应而非主动推动",
        })

    score = max(0, min(100, int(ratio * 100) + 30))
    return {"score": score, "initiative_ratio": round(ratio, 3), "issues": issues}


def _check_le_overuse(text: str) -> dict:
    """"了"字密度检测。"""
    chinese_chars = _char_count(text)
    if chinese_chars == 0:
        return {"score": 100, "issues": []}

    le_count = text.count("了")
    density_per_1000 = (le_count / chinese_chars) * 1000

    issues: list[dict] = []
    if density_per_1000 > LE_PER_1000_THRESHOLD:
        issues.append({
            "type": "le_overuse",
            "severity": "medium",
            "reason": f""了"字密度={density_per_1000:.1f}‰（>{LE_PER_1000_THRESHOLD}‰），"
                       f"语气助词'了'使用过于频繁，文本节奏拖沓",
        })

    score = max(0, min(100, int(100 - max(0, density_per_1000 - 10) * 1.5)))
    return {"score": score, "density_per_1000": round(density_per_1000, 1), "issues": issues}


def _check_idiom_density(paragraphs: list[str]) -> dict:
    """成语密度与分布检测。"""
    issues: list[dict] = []
    total_idiom_count = 0

    for i, p_text in enumerate(paragraphs):
        chinese_chars = _char_count(p_text)
        if chinese_chars < 10:
            continue

        # 用滑动窗口检测 4 字成语
        idiom_in_para: list[str] = []
        for j in range(len(p_text) - 3):
            chunk = p_text[j:j + 4]
            if chunk in _COMMON_IDIOMS:
                idiom_in_para.append(chunk)
                total_idiom_count += 1

        if len(idiom_in_para) > IDIOM_PER_PARAGRAPH_THRESHOLD:
            unique_idioms = list(set(idiom_in_para))
            issues.append({
                "type": "idiom_pileup",
                "severity": "medium",
                "reason": f"第 {i + 1} 段堆积 {len(idiom_in_para)} 个成语: {', '.join(unique_idioms[:6])}",
            })

    score = max(0, min(100, 100 - len(issues) * 15))
    return {"score": score, "total_idiom_count": total_idiom_count, "issues": issues}


def _check_show_tell_ratio(sentences: list[str]) -> dict:
    """展示/告知比检测。"""
    if len(sentences) < 5:
        return {"score": 100, "issues": []}

    show_count = sum(
        1 for s in sentences
        if any(kw in s for kw in _VISUAL_SENSORY_WORDS)
    )
    tell_count = sum(
        1 for s in sentences
        if any(kw in s for kw in _ABSTRACT_JUDGMENT_WORDS)
    )

    ratio = show_count / max(tell_count, 1)

    issues: list[dict] = []
    if ratio < SHOW_TELL_MIN_RATIO:
        issues.append({
            "type": "show_tell_imbalance",
            "severity": "medium",
            "reason": f"展示/告知比={ratio:.1f}（<{SHOW_TELL_MIN_RATIO:.1f}），"
                       f"展示句={show_count}，告知句={tell_count}，文本偏向告知而非展示",
        })

    score = max(0, min(100, int(ratio / 2.0 * 100)))
    return {"score": score, "ratio": round(ratio, 2), "show_count": show_count,
            "tell_count": tell_count, "issues": issues}


def _detect_protagonist_name(text: str, project_dir: Path | None = None) -> str:
    """从文本/角色档案中尝试检测主角名。"""
    # 先尝试从角色档案读取
    if project_dir:
        chars_path = project_dir / "00_memory" / "characters.md"
        schema_path = project_dir / "00_memory" / "schema" / "characters.json"
        if schema_path.exists():
            try:
                chars_data = json.loads(schema_path.read_text(encoding="utf-8"))
                for char in chars_data.get("characters", []):
                    if isinstance(char, dict) and char.get("role") == "protagonist":
                        return str(char.get("name", ""))
            except (json.JSONDecodeError, KeyError):
                pass
        if chars_path.exists():
            content = chars_path.read_text(encoding="utf-8")
            m = re.search(r"主角[：:]\s*[|｜]?\s*([\u4e00-\u9fff]{2,4})", content)
            if m:
                return m.group(1).strip()

    # 回退：取前 500 字中出现频率最高的 2-3 字中文名
    head = text[:500]
    name_counter: Counter[str] = Counter()
    for m in _PROTAGONIST_NAME_PATTERN.finditer(head):
        name = m.group(0)
        # 排除常见非名字词
        if name in ("的时候", "已经", "那个", "这个", "不是", "因为", "所以",
                     "一下", "一样", "什么", "怎么", "可以", "没有", "出来",
                     "起来", "下来", "过来", "上去", "下去", "过去", "回来",
                     "回去", "进来", "进去", "出来", "出去", "知道", "觉得"):
            continue
        name_counter[name] += 1
    top = name_counter.most_common(1)
    return top[0][0] if top else ""


# ---------------------------------------------------------------------------
# 主审计函数
# ---------------------------------------------------------------------------

def analyze_naturalness(
    text: str,
    *,
    project_dir: Path | None = None,
    silence: bool = False,
) -> dict:
    """
    对章节正文做中文自然度结构分析。

    Args:
        text: 章节正文（纯文本）
        project_dir: 项目根目录（可选，用于读取角色档案检测主角名）
        silence: 是否抑制控制台输出

    Returns:
        {
            "verdict": "pass" | "warn" | "rewrite",
            "scores": { dimension: score, ... },
            "issues": [{ type, severity, reason }, ...],
            "summary": str,
        }
    """
    sentences = _extract_sentences(text)
    paragraphs = _extract_paragraphs(text)
    protagonist_name = _detect_protagonist_name(text, project_dir)

    all_issues: list[dict] = []
    scores: dict[str, int] = {}

    # 逐维度检测
    checks = [
        ("sentence_rhythm", _check_sentence_rhythm(sentences)),
        ("sentence_openings", _check_sentence_openings(sentences)),
        ("paragraph_pattern", _check_paragraph_pattern(paragraphs)),
        ("transition_density", _check_transition_overuse(text)),
        ("visual_beat", _check_visual_beat_coverage(sentences)),
        ("inner_monologue", _check_inner_monologue_ratio(sentences)),
        ("dialogue_initiative", _check_dialogue_initiative(text, protagonist_name)),
        ("le_density", _check_le_overuse(text)),
        ("idiom_density", _check_idiom_density(paragraphs)),
        ("show_tell_ratio", _check_show_tell_ratio(sentences)),
    ]

    for dim_name, result in checks:
        scores[dim_name] = result["score"]
        all_issues.extend(result.get("issues", []))

    # 综合裁决
    high_severity = [i for i in all_issues if i["severity"] == "high"]
    medium_severity = [i for i in all_issues if i["severity"] == "medium"]
    avg_score = sum(scores.values()) / len(scores) if scores else 100

    if high_severity or avg_score < 40:
        verdict = "rewrite"
    elif medium_severity or avg_score < 60:
        verdict = "warn"
    else:
        verdict = "pass"

    # 摘要
    chinese_chars = _char_count(text)
    dimension_names = {
        "sentence_rhythm": "句长节奏熵",
        "sentence_openings": "句首多样性",
        "paragraph_pattern": "段落结构",
        "transition_density": "过渡词密度",
        "visual_beat": "视觉节拍",
        "inner_monologue": "内心独白",
        "dialogue_initiative": "对话主动性",
        "le_density": ""了"字密度",
        "idiom_density": "成语分布",
        "show_tell_ratio": "展示/告知比",
    }
    summary_lines = [f"中文自然度分析 — 总字数 {chinese_chars}"]
    for dim_name, score in scores.items():
        cn_name = dimension_names.get(dim_name, dim_name)
        flag = " ⚠" if score < 50 else ""
        summary_lines.append(f"  {cn_name}: {score}{flag}")

    result = {
        "verdict": verdict,
        "target_chapter": None,
        "total_chars": chinese_chars,
        "scores": scores,
        "issues": all_issues,
        "issue_count": len(all_issues),
        "high_issue_count": len(high_severity),
        "protagonist_detected": protagonist_name,
        "summary": "\n".join(summary_lines),
    }

    if not silence:
        print(result["summary"])
        if all_issues:
            print(f"\n发现 {len(all_issues)} 个自然度问题:")
            for issue in all_issues:
                print(f"  [{issue['severity']}] {issue['reason']}")

    return result


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def _resolve_chapter_path(project_dir: Path, chapter: int) -> Path:
    """在项目目录中查找章节文件。"""
    # 尝试多种命名约定
    from pathlib import Path as _Path
    candidates = [
        project_dir / "02_chapters" / f"ch{chapter:03d}.md",
        project_dir / "02_first_draft" / f"ch{chapter:03d}.md",
        project_dir / "02_first_draft" / f"ch{chapter}.md",
    ]
    # 也搜索 02_first_draft 下的模糊匹配
    draft_dir = project_dir / "02_first_draft"
    if draft_dir.exists():
        for f in sorted(draft_dir.glob(f"ch{chapter:03d}*.md")):
            candidates.append(f)
        for f in sorted(draft_dir.glob(f"ch{chapter}*.md")):
            candidates.append(f)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"找不到第 {chapter} 章的正文文件")


def main() -> None:
    parser = argparse.ArgumentParser(description="中文自然度分析 — 检测章节语言质感")
    parser.add_argument("--project", type=str, required=True, help="项目根目录路径")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--text", type=str, default=None, help="直接传入文本（用于测试）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not project_dir.exists():
        print(f"项目目录不存在: {project_dir}")
        return

    if args.text:
        text = args.text
    else:
        chapter_path = _resolve_chapter_path(project_dir, args.chapter)
        text = chapter_path.read_text(encoding="utf-8")

    result = analyze_naturalness(text, project_dir=project_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
