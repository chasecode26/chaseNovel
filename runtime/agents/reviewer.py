from __future__ import annotations

import json
import re
from pathlib import Path

from evaluators.prose_concreteness import from_runtime_output as from_prose_concreteness_runtime_output
from runtime.contracts import EvaluatorVerdict
from runtime.agents.handoff import write_reviewer_handoff
from runtime.agents.market_assets import compact_asset_lines, load_market_assets
from runtime.agents.prompt_loader import load_agent_prompt, write_agent_prompt_snapshot


class ReviewerAgent:
    """Reviews prose quality without rewriting the manuscript."""

    name = "ReviewerAgent"

    def _coerce_verdict(self, payload: dict[str, object]) -> EvaluatorVerdict:
        return EvaluatorVerdict(
            dimension=str(payload.get("dimension", "unknown")),
            status=str(payload.get("status", "pass")),
            blocking=bool(payload.get("blocking", False)),
            evidence=[str(item) for item in payload.get("evidence", []) if str(item).strip()],
            why_it_breaks=str(payload.get("why_it_breaks", "")).strip(),
            minimal_fix=str(payload.get("minimal_fix", "")).strip(),
            rewrite_scope=str(payload.get("rewrite_scope", "")).strip(),
        )

    def review(self, draft_payload: dict[str, object]) -> list[EvaluatorVerdict]:
        return [
            self._coerce_verdict(from_prose_concreteness_runtime_output(draft_payload)),
            self._story_logic_verdict(draft_payload),
            self._hook_integrity_verdict(draft_payload),
            self._scene_density_verdict(draft_payload),
            self._continuity_guardrail_verdict(draft_payload),
            self._market_fit_verdict(draft_payload),
            self._pre_publish_checklist_verdict(draft_payload),
            self._expectation_integrity_verdict(draft_payload),
            self._genre_framework_fit_verdict(draft_payload),
            self._opening_diagnostics_verdict(draft_payload),
        ]

    def review_with_report(
        self,
        project_dir: Path,
        chapter: int,
        draft_payload: dict[str, object],
    ) -> tuple[list[EvaluatorVerdict], dict[str, str]]:
        agent_prompt = load_agent_prompt("reviewer-agent")
        market_assets = load_market_assets(project_dir)
        prompt_path = write_agent_prompt_snapshot(project_dir, chapter, "reviewer-agent", agent_prompt)
        verdicts = self.review(draft_payload)
        report_paths = self._write_review_report(project_dir, chapter, verdicts, agent_prompt, market_assets)
        if prompt_path:
            report_paths["reviewer_agent_prompt"] = prompt_path
        handoff_paths = write_reviewer_handoff(
            project_dir,
            chapter,
            draft_payload=draft_payload,
            verdicts=[item.to_dict() for item in verdicts],
            paths=report_paths,
        )
        report_paths.update(handoff_paths)
        return verdicts, report_paths

    def _write_review_report(
        self,
        project_dir: Path,
        chapter: int,
        verdicts: list[EvaluatorVerdict],
        agent_prompt: str,
        market_assets: dict[str, str],
    ) -> dict[str, str]:
        review_dir = project_dir / "04_gate" / f"ch{chapter:03d}"
        review_dir.mkdir(parents=True, exist_ok=True)
        json_path = review_dir / "reviewer_agent_report.json"
        md_path = review_dir / "reviewer_agent_report.md"
        payload = {
            "agent": self.name,
            "chapter": chapter,
            "prompt_preview": "\n".join(agent_prompt.splitlines()[:10]),
            "verdicts": [item.to_dict() for item in verdicts],
            "blocking_dimensions": [item.dimension for item in verdicts if item.blocking],
            "advisory_dimensions": [item.dimension for item in verdicts if not item.blocking and item.status == "warn"],
            "quality_gate": {
                "must_rewrite": any(item.blocking for item in verdicts),
                "first_blocking_dimension": next((item.dimension for item in verdicts if item.blocking), ""),
                "rewrite_scopes": [item.rewrite_scope for item in verdicts if item.blocking and item.rewrite_scope],
            },
            "market_assets": {
                "platform_profile_loaded": bool(market_assets.get("platform_profile")),
                "prose_examples_loaded": bool(market_assets.get("prose_examples")),
                "pre_publish_checklist_loaded": bool(market_assets.get("pre_publish_checklist")),
                "platform_profile_preview": compact_asset_lines(market_assets.get("platform_profile", ""), limit=8),
                "pre_publish_checklist_preview": compact_asset_lines(market_assets.get("pre_publish_checklist", ""), limit=8),
            },
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lines = [
            "# ReviewerAgent Report",
            "",
            f"- agent: {self.name}",
            f"- chapter: {chapter}",
            f"- blocking_dimensions: {', '.join(payload['blocking_dimensions']) or 'none'}",
            f"- advisory_dimensions: {', '.join(payload['advisory_dimensions']) or 'none'}",
            f"- must_rewrite: {'yes' if payload['quality_gate']['must_rewrite'] else 'no'}",
            f"- platform_profile_loaded: {'yes' if payload['market_assets']['platform_profile_loaded'] else 'no'}",
            f"- pre_publish_checklist_loaded: {'yes' if payload['market_assets']['pre_publish_checklist_loaded'] else 'no'}",
            "",
            "## Verdicts",
        ]
        for verdict in verdicts:
            lines.extend(
                [
                    f"### {verdict.dimension}",
                    f"- status: {verdict.status}",
                    f"- blocking: {'yes' if verdict.blocking else 'no'}",
                    f"- rewrite_scope: {verdict.rewrite_scope or 'none'}",
                    f"- minimal_fix: {verdict.minimal_fix or 'none'}",
                    "- evidence:",
                ]
            )
            lines.extend(f"  - {item}" for item in verdict.evidence or ["none"])
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {
            "reviewer_agent_report_json": json_path.as_posix(),
            "reviewer_agent_report_markdown": md_path.as_posix(),
        }

    def _load_manuscript(self, draft_payload: dict[str, object]) -> str:
        path = Path(str(draft_payload.get("manuscript_path", "")).strip())
        if not str(path).strip() or not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _story_logic_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        scene_cards = [item for item in draft_payload.get("scene_cards", []) if isinstance(item, dict)]
        outcome = draft_payload.get("outcome_signature", {})
        outcome = outcome if isinstance(outcome, dict) else {}
        evidence: list[str] = []

        if not scene_cards:
            evidence.append("缺少 scene_cards，无法复核场景目标、反转和代价链。")
        else:
            result_types = {str(item.get("result_type", "")).strip() for item in scene_cards if str(item.get("result_type", "")).strip()}
            cost_types = {str(item.get("cost_type", "")).strip() for item in scene_cards if str(item.get("cost_type", "")).strip()}
            if len(scene_cards) >= 3 and len(result_types) <= 1:
                evidence.append("多个场景 result_type 单一，故事推进容易像重复拍点。")
            if len(scene_cards) >= 3 and len(cost_types) <= 1:
                evidence.append("多个场景 cost_type 单一，胜利代价不够分层。")
        if not str(outcome.get("chapter_result", "")).strip():
            evidence.append("outcome_signature 缺少 chapter_result，章末局面变化不够明确。")
        if not str(outcome.get("next_pull", "")).strip():
            evidence.append("outcome_signature 缺少 next_pull，追读牵引不足。")

        return EvaluatorVerdict(
            dimension="story_logic",
            status="fail" if len(evidence) >= 2 else ("warn" if evidence else "pass"),
            blocking=len(evidence) >= 2,
            evidence=evidence,
            why_it_breaks="场景目标、结果和代价如果不能形成链条，正文会只剩片段化情绪，读者追读问题不成立。",
            minimal_fix="回到 SceneBeatPlan：补清每场目标、反转、代价和下一场牵引，确保 chapter_result 与 next_pull 同时落地。",
            rewrite_scope="scene_beat_plan + chapter_result",
        )

    def _hook_integrity_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        text = self._load_manuscript(draft_payload)
        outcome = draft_payload.get("outcome_signature", {})
        outcome = outcome if isinstance(outcome, dict) else {}
        next_pull = str(outcome.get("next_pull", "")).strip()
        hook_type = str(outcome.get("hook_type", "")).strip()
        tail = "\n".join([line for line in text.splitlines() if line.strip()][-5:])
        evidence: list[str] = []

        if not tail.strip():
            evidence.append("正文尾段为空，无法形成章尾钩子。")
        if next_pull and next_pull not in tail and len(next_pull) <= 40:
            evidence.append("章尾没有明显承接 outcome_signature.next_pull。")
        if not hook_type:
            evidence.append("outcome_signature 缺少 hook_type。")
        if tail and not re.search(r"[？?！!。][”\"』」]?$", tail.strip()):
            evidence.append("尾段收束标点异常，章尾落点可能没有形成有效停顿。")
        if tail and not any(token in tail for token in ("门", "声", "手", "眼", "血", "雨", "灯", "代价", "下一", "停", "问")):
            evidence.append("章尾缺少可感知的物件、动作或代价信号，悬念偏虚。")

        blocking = len(evidence) >= 2
        return EvaluatorVerdict(
            dimension="hook_integrity",
            status="fail" if blocking else ("warn" if evidence else "pass"),
            blocking=blocking,
            evidence=evidence,
            why_it_breaks="章尾如果只有信息悬念，没有动作、代价或关系裂缝，读者不会产生下一章冲动。",
            minimal_fix="只修章尾：补一个具体动作/物件落点，再把 next_pull 落成表层事件钩子和里层代价钩子。",
            rewrite_scope="chapter_tail",
        )

    def _scene_density_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        scene_beat_plan = draft_payload.get("scene_beat_plan", {})
        scene_cards = [item for item in draft_payload.get("scene_cards", []) if isinstance(item, dict)]
        beats = scene_beat_plan.get("beats", []) if isinstance(scene_beat_plan, dict) else []
        evidence: list[str] = []

        if beats and scene_cards and len(scene_cards) < min(3, len(beats)):
            evidence.append("scene_cards 少于 SceneBeatPlan 的最低承载量，正文可能压缩掉关键交锋。")
        if scene_cards:
            for index, item in enumerate(scene_cards, start=1):
                summary = str(item.get("summary", "")).strip()
                if len(summary) < 6:
                    evidence.append(f"第 {index} 场 summary 过短，场景功能不清。")
                    break
        if not beats:
            evidence.append("缺少 SceneBeatPlan，Writer 直接从章卡跳正文，稳定性不足。")

        return EvaluatorVerdict(
            dimension="scene_density",
            status="fail" if len(evidence) >= 2 else ("warn" if evidence else "pass"),
            blocking=len(evidence) >= 2,
            evidence=evidence,
            why_it_breaks="没有 SceneBeatPlan 或场景承载不足时，正文容易变成概述而不是连续戏剧动作。",
            minimal_fix="补齐 SceneBeatPlan 与 scene_cards 对齐关系，让每场至少承担一个交锋、一个变化和一个代价。",
            rewrite_scope="scene_beat_plan",
        )

    def _continuity_guardrail_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        scene_beat_plan = draft_payload.get("scene_beat_plan", {})
        beats = scene_beat_plan.get("beats", []) if isinstance(scene_beat_plan, dict) else []
        evidence: list[str] = []
        if not beats:
            evidence.append("缺少 SceneBeatPlan，无法复核设定、时间线和伏笔边界。")
        else:
            if any(not str(item.get("timeline_guardrail", "")).strip() for item in beats if isinstance(item, dict)):
                evidence.append("存在 beat 缺少 timeline_guardrail，时间线风险没有前置锁定。")
            if any(not str(item.get("setting_guardrail", "")).strip() for item in beats if isinstance(item, dict)):
                evidence.append("存在 beat 缺少 setting_guardrail，可能用新设定偷解问题。")
            if any(not str(item.get("foreshadow_or_payoff", "")).strip() for item in beats if isinstance(item, dict)):
                evidence.append("存在 beat 缺少 foreshadow_or_payoff，伏笔/回收处理不明确。")
        return EvaluatorVerdict(
            dimension="continuity_guardrail",
            status="fail" if len(evidence) >= 2 else ("warn" if evidence else "pass"),
            blocking=len(evidence) >= 2,
            evidence=evidence,
            why_it_breaks="设定、时间线、知情边界和伏笔回收如果不前置锁定，正文很容易靠临时发明推进。",
            minimal_fix="回到 SceneBeatAgent：补齐 timeline_guardrail、setting_guardrail、foreshadow_or_payoff，再交给 WriterAgent。",
            rewrite_scope="scene_beat_plan + continuity_guardrails",
        )

    def _market_fit_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        scene_beat_plan = draft_payload.get("scene_beat_plan", {})
        beats = scene_beat_plan.get("beats", []) if isinstance(scene_beat_plan, dict) else []
        outcome = draft_payload.get("outcome_signature", {})
        outcome = outcome if isinstance(outcome, dict) else {}
        evidence: list[str] = []
        if beats and any(not str(item.get("market_reader_hook", "")).strip() for item in beats if isinstance(item, dict)):
            evidence.append("存在 beat 缺少 market_reader_hook，场景末端追读牵引不足。")
        if not str(outcome.get("next_pull", "")).strip():
            evidence.append("缺少 next_pull，平台连载的章尾追读问题不成立。")
        if not str(outcome.get("cost_type", "")).strip():
            evidence.append("缺少 cost_type，爽点代价不明确，容易变成轻飘飘的赢。")
        project_dir = Path(str(draft_payload.get("project", "")).strip() or ".")
        platform_profile = load_market_assets(project_dir).get("platform_profile", "")
        if "番茄" not in platform_profile or "七猫" not in platform_profile:
            evidence.append("缺少番茄/七猫平台画像，market_fit 只能做通用判断，无法按目标平台口味收紧。")
        return EvaluatorVerdict(
            dimension="market_fit",
            status="fail" if len(evidence) >= 2 else ("warn" if evidence else "pass"),
            blocking=len(evidence) >= 2,
            evidence=evidence,
            why_it_breaks="平台读者追更依赖清晰的下一步问题、代价和场景末端牵引，缺失时章节容易读完即散。",
            minimal_fix="补齐每场 market_reader_hook、章尾 next_pull 和胜利代价，再重写对应场景或章尾。",
            rewrite_scope="scene_beat_plan + chapter_tail",
        )

    def _pre_publish_checklist_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        text = self._load_manuscript(draft_payload)
        outcome = draft_payload.get("outcome_signature", {})
        outcome = outcome if isinstance(outcome, dict) else {}
        scene_cards = [item for item in draft_payload.get("scene_cards", []) if isinstance(item, dict)]
        evidence: list[str] = []

        clean_lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        opening = "".join(clean_lines[:4])
        tail = "\n".join(clean_lines[-5:])
        banned_terms = ("runtime", "agent", "scene", "beat", "爽点", "节奏", "伏笔", "质量门", "Reviewer", "Writer")
        if opening and not any(token in opening for token in ("“", "”", "。", "！", "？")):
            evidence.append("开章缺少可读的动作/对白/异常落点，可能没有在 300 字内入戏。")
        if not scene_cards:
            evidence.append("缺少 scene_cards，无法确认目标、冲突、结果、代价是否逐场落地。")
        if not str(outcome.get("chapter_result", "")).strip():
            evidence.append("缺少 chapter_result，本章可见推进不明确。")
        if not str(outcome.get("next_pull", "")).strip():
            evidence.append("缺少 next_pull，读完后下一章问题不清楚。")
        if any(term in text for term in banned_terms):
            evidence.append("正文疑似混入创作术语，需要改回故事内部语言。")
        if tail and not any(token in tail for token in ("门", "手", "血", "灯", "信", "名字", "账", "代价", "钥匙", "声音")):
            evidence.append("章尾缺少可感知物件、动作或代价信号，钩子可能偏虚。")

        blocking = len(evidence) >= 2
        return EvaluatorVerdict(
            dimension="pre_publish_checklist",
            status="fail" if blocking else ("warn" if evidence else "pass"),
            blocking=blocking,
            evidence=evidence,
            why_it_breaks="发稿前清单失败时，章节可能能读完但追读理由不够硬，尤其会伤害番茄/七猫的推荐流留存。",
            minimal_fix="按发稿前清单补开章入戏、本章推进、章尾 next_pull、场景代价和故事内语言。",
            rewrite_scope="opening + scene_beat_plan + chapter_tail",
        )

    def _expectation_integrity_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        scene_beat_plan = draft_payload.get("scene_beat_plan", {})
        beats = scene_beat_plan.get("beats", []) if isinstance(scene_beat_plan, dict) else []
        outcome = draft_payload.get("outcome_signature", {})
        outcome = outcome if isinstance(outcome, dict) else {}
        evidence: list[str] = []

        if not beats:
            evidence.append("缺少 SceneBeatPlan，无法检查短期待、长期待、兑现和新挂期待。")
        else:
            if any(not str(item.get("short_expectation", "")).strip() for item in beats if isinstance(item, dict)):
                evidence.append("存在 beat 缺少 short_expectation，读者当场想看的问题不明确。")
            if any(not str(item.get("new_expectation", "")).strip() for item in beats if isinstance(item, dict)):
                evidence.append("存在 beat 缺少 new_expectation，爽点后可能断期待。")
            if any(not str(item.get("expectation_gap_risk", "")).strip() for item in beats if isinstance(item, dict)):
                evidence.append("存在 beat 缺少 expectation_gap_risk，断期待风险没有前置识别。")
        if not str(outcome.get("next_pull", "")).strip():
            evidence.append("缺少 outcome_signature.next_pull，章尾没有明确新期待。")

        blocking = len(evidence) >= 2
        return EvaluatorVerdict(
            dimension="expectation_integrity",
            status="fail" if blocking else ("warn" if evidence else "pass"),
            blocking=blocking,
            evidence=evidence,
            why_it_breaks="期待线断档时，读者会在爽点兑现或信息解释后自然停下，不会形成下一章点击。",
            minimal_fix="补齐短期待、长期待、兑现点和新挂期待，尤其让章尾 next_pull 承接本章结果。",
            rewrite_scope="scene_beat_plan + chapter_tail",
        )

    def _genre_framework_fit_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        scene_beat_plan = draft_payload.get("scene_beat_plan", {})
        beats = scene_beat_plan.get("beats", []) if isinstance(scene_beat_plan, dict) else []
        evidence: list[str] = []
        if not beats:
            evidence.append("缺少 SceneBeatPlan，无法检查题材框架是否落到场景。")
        elif any(not str(item.get("genre_framework_hint", "")).strip() for item in beats if isinstance(item, dict)):
            evidence.append("存在 beat 缺少 genre_framework_hint，章节看点可能偏离题材承诺。")

        text = self._load_manuscript(draft_payload)
        if text.count("设定") + text.count("规则") >= 6 and text.count("“") < 4:
            evidence.append("正文设定/规则密度偏高，但对白和行动不足，题材承诺可能变成说明书。")

        return EvaluatorVerdict(
            dimension="genre_framework_fit",
            status="fail" if len(evidence) >= 2 else ("warn" if evidence else "pass"),
            blocking=len(evidence) >= 2,
            evidence=evidence,
            why_it_breaks="题材承诺偏移会让读者不知道该期待什么，尤其影响番茄/七猫的前期留存。",
            minimal_fix="回到题材框架：明确本章兑现的是系统反馈、复仇打脸、都市逆袭、升级展示、感情拉扯或其他核心看点。",
            rewrite_scope="genre_framework + scene_beat_plan",
        )

    def _opening_diagnostics_verdict(self, draft_payload: dict[str, object]) -> EvaluatorVerdict:
        text = self._load_manuscript(draft_payload)
        chapter = int(draft_payload.get("chapter", 0) or 0)
        clean_lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        opening = "".join(clean_lines[:5])
        evidence: list[str] = []
        if chapter not in {0, 1} and "第001" not in text[:40] and "Chapter 001" not in text[:40]:
            return EvaluatorVerdict(
                dimension="opening_diagnostics",
                status="pass",
                blocking=False,
                evidence=[],
                why_it_breaks="",
                minimal_fix="",
                rewrite_scope="",
            )
        if not opening:
            evidence.append("开篇为空，无法完成黄金一章诊断。")
        if opening and len(opening) > 300 and not any(token in opening[:300] for token in ("“", "！”", "？", "门", "血", "响", "跑", "推", "抓")):
            evidence.append("前 300 字缺少明显动作、对白、异常、危机或冲突对象。")
        opening_head = opening[:500]
        if (
            any(token in opening_head for token in ("等级体系", "势力分布", "家族历史", "世界背景"))
            or opening_head.count("规则") >= 2
            or opening_head.count("设定") >= 2
        ):
            evidence.append("开篇疑似优先释放设定说明，压过危机/目标。")

        blocking = bool(evidence) if chapter in {0, 1} else len(evidence) >= 2
        return EvaluatorVerdict(
            dimension="opening_diagnostics",
            status="fail" if blocking else ("warn" if evidence else "pass"),
            blocking=blocking,
            evidence=evidence,
            why_it_breaks="第一章或阶段开篇没有快速交付吸睛、人设、卖点和危机时，读者会在进入正文前离开。",
            minimal_fix="把前 300 字改成动作/对白/异常/危机入场，并把设定说明后移到事件中释放。",
            rewrite_scope="opening",
        )
