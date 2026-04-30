# RewriterAgent Handoff

## Mission
Repair only the scope named by RewriteBrief.

## Inputs
- Original manuscript snapshot.
- ReviewerAgent report.
- RewriteBrief.
- SceneBeatPlan.
- WriterAgent prompt and chapter direction.

## Local Surgery Rules
- `chapter_tail`: replace only the ending paragraphs.
- `dialogue`: replace only dialogue-bearing paragraphs.
- `flagged_paragraphs`: replace only paragraphs with abstract/summary markers.
- `scene_beat_plan`: repair scene structure before touching prose.

## Completion Standard
- Preserve working scene pressure and character actions.
- Remove the named blocking issue.
- Do not create new continuity, character, or hook problems.
