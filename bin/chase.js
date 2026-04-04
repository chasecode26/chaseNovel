#!/usr/bin/env node
"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

function main() {
  const argv = process.argv.slice(2);
  const { command, options, passthrough } = parseArgs(argv);
  const repoRoot = path.resolve(__dirname, "..");
  const python = process.env.PYTHON || "python";

  if (command === "help" || command === "--help" || command === "-h") {
    printHelp();
    return;
  }

  if (command === "gate") {
    runPython(python, path.join(repoRoot, "scripts", "chapter_gate.py"), passthrough);
    return;
  }

  if (command === "batch") {
    runPython(python, path.join(repoRoot, "scripts", "batch_gate.py"), passthrough);
    return;
  }

  if (command === "audit") {
    runPython(python, path.join(repoRoot, "scripts", "language_audit.py"), passthrough);
    return;
  }

  if (command === "context") {
    runPython(python, path.join(repoRoot, "scripts", "context_compiler.py"), passthrough);
    return;
  }

  if (command === "foreshadow") {
    runPython(python, path.join(repoRoot, "scripts", "foreshadow_scheduler.py"), passthrough);
    return;
  }

  if (command === "dashboard") {
    runPython(python, path.join(repoRoot, "scripts", "dashboard_snapshot.py"), passthrough);
    return;
  }

  if (command === "arc") {
    runPython(python, path.join(repoRoot, "scripts", "arc_tracker.py"), passthrough);
    return;
  }

  if (command === "timeline") {
    runPython(python, path.join(repoRoot, "scripts", "timeline_check.py"), passthrough);
    return;
  }

  if (command === "repeat") {
    runPython(python, path.join(repoRoot, "scripts", "anti_repeat_scan.py"), passthrough);
    return;
  }

  if (command === "bootstrap") {
    runPython(python, path.join(repoRoot, "scripts", "project_bootstrap.py"), passthrough);
    return;
  }

  if (command === "memory") {
    runPython(python, path.join(repoRoot, "scripts", "memory_update.py"), passthrough);
    return;
  }

  if (command === "run") {
    runPython(python, path.join(repoRoot, "scripts", "workflow_runner.py"), passthrough);
    return;
  }

  if (command === "doctor") {
    runPython(python, path.join(repoRoot, "scripts", "project_doctor.py"), passthrough);
    return;
  }

  printHelp(`Unknown command: ${command}`);
  process.exitCode = 1;
}

function parseArgs(argv) {
  const [command = "help", ...rest] = argv;
  const options = { project: "." };
  const passthrough = [];

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (token === "--project") {
      options.project = rest[index + 1];
      passthrough.push(token, rest[index + 1]);
      index += 1;
      continue;
    }
    passthrough.push(token);
  }

  if (!passthrough.includes("--project") && command !== "help") {
    passthrough.unshift(options.project);
    passthrough.unshift("--project");
  }

  return { command, options, passthrough };
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
  chase run --project <dir> [--chapter <n>] [--steps <csv>]

Notes:
  - existing gate and audit scripts are passed through unchanged
  - default run steps: doctor,context,memory,foreshadow,arc,timeline,repeat,dashboard
  - chase run --chapter expects an already drafted chapter number; do not pass the next unwritten chapter
  - project defaults to the current directory`);
}

main();
