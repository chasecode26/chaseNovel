#!/usr/bin/env node
"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

const COMMAND_SPECS = {
  gate: { script: "chapter_gate.py" },
  planning: { script: "chapter_planning_review.py" },
  batch: { script: "batch_gate.py" },
  audit: { script: "language_audit.py" },
  context: { script: "context_compiler.py" },
  foreshadow: { script: "foreshadow_scheduler.py" },
  dashboard: { script: "dashboard_snapshot.py" },
  arc: { script: "arc_tracker.py" },
  timeline: { script: "timeline_check.py" },
  repeat: { script: "anti_repeat_scan.py" },
  bootstrap: { script: "project_bootstrap.py" },
  memory: { script: "memory_update.py" },
  run: { script: "workflow_runner.py" },
  doctor: { script: "project_doctor.py" },
  check: {
    script: "workflow_runner.py",
    injectArgs: ["--dry-run", "--steps", "doctor,planning,context,foreshadow,arc,timeline,repeat,dashboard"],
  },
};

function main() {
  const argv = process.argv.slice(2);
  const { command, passthrough } = parseArgs(argv);
  const repoRoot = path.resolve(__dirname, "..");
  const python = process.env.PYTHON || "python";

  if (command === "help" || command === "--help" || command === "-h") {
    printHelp();
    return;
  }

  const spec = COMMAND_SPECS[command];
  if (spec) {
    const args = mergeArgs(spec.injectArgs || [], passthrough);
    runPython(python, path.join(repoRoot, "scripts", spec.script), args);
    return;
  }

  printHelp(`Unknown command: ${command}`);
  process.exitCode = 1;
}

function parseArgs(argv) {
  const [command = "help", ...rest] = argv;
  const passthrough = [];

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (token === "--project") {
      passthrough.push(token, rest[index + 1]);
      index += 1;
      continue;
    }
    passthrough.push(token);
  }

  if (!passthrough.includes("--project") && command !== "help") {
    passthrough.unshift(".");
    passthrough.unshift("--project");
  }

  return { command, passthrough };
}

function mergeArgs(injectedArgs, passthrough) {
  if (!injectedArgs.length) {
    return passthrough;
  }

  const merged = [...passthrough];
  for (let index = 0; index < injectedArgs.length; index += 1) {
    const token = injectedArgs[index];
    const nextToken = injectedArgs[index + 1];
    const isOption = token.startsWith("--");
    const hasValue = isOption && nextToken && !nextToken.startsWith("--");

    if (hasValue) {
      if (!merged.includes(token)) {
        merged.unshift(nextToken);
        merged.unshift(token);
      }
      index += 1;
      continue;
    }

    if (!merged.includes(token)) {
      merged.unshift(token);
    }
  }
  return merged;
}

function runPython(python, scriptPath, args) {
  const result = spawnSync(python, [scriptPath, ...args], { stdio: "inherit" });
  if (result.error) {
    throw result.error;
  }
  process.exitCode = result.status || 0;
}

function printHelp(errorMessage) {
  if (errorMessage) {
    console.error(errorMessage);
  }
  console.log(`Usage:
  chase planning --project <dir> [--chapter <n> | --target-chapter <n>]
  chase context --project <dir> [--chapter <n>]
  chase foreshadow --project <dir> [--chapter <n>]
  chase dashboard --project <dir>
  chase arc --project <dir>
  chase timeline --project <dir>
  chase repeat --project <dir>
  chase memory --project <dir> [--chapter <n>]
  chase gate --project <dir> [--chapter-no <n>]
  chase batch --project <dir> [--from <n> --to <n>]
  chase audit --project <dir> [--chapter-no <n>]
  chase bootstrap --project <dir> [--force]
  chase doctor --project <dir> [--json]
  chase check --project <dir> [--chapter <n>]
  chase run --project <dir> [--chapter <n>] [--steps <csv>]

Notes:
  - planning reviews the next chapter by default; --chapter means current drafted chapter
  - existing gate and audit scripts are passed through unchanged
  - check is a dry-run health sweep: doctor + planning + context + foreshadow + arc + timeline + repeat + dashboard
  - check keeps planning blockers strict; a freshly bootstrapped but unplanned project is expected to fail
  - default run steps: doctor,planning,context,memory,foreshadow,arc,timeline,repeat,dashboard
  - chase run --chapter expects an already drafted chapter number; do not pass the next unwritten chapter
  - project defaults to the current directory`);
}

main();
