#!/usr/bin/env node
"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

const COMMAND_SPECS = {
  open: { script: "open_book.py" },
  quality: { script: "quality_gate.py" },
  gate: { script: "quality_gate.py", injectArgs: ["--check", "chapter"] },
  draft: { script: "quality_gate.py", injectArgs: ["--check", "draft"] },
  planning: { script: "planning_context.py" },
  write: { script: "engine_runner.py" },
  status: { script: "book_health.py" },
  batch: { script: "quality_gate.py", injectArgs: ["--check", "batch"] },
  audit: { script: "quality_gate.py", injectArgs: ["--check", "language"] },
  context: { script: "planning_context.py" },
  foreshadow: { script: "book_health.py", injectArgs: ["--focus", "foreshadow"] },
  dashboard: { script: "book_health.py", injectArgs: ["--focus", "dashboard"] },
  arc: { script: "book_health.py", injectArgs: ["--focus", "arc"] },
  timeline: { script: "book_health.py", injectArgs: ["--focus", "timeline"] },
  repeat: { script: "book_health.py", injectArgs: ["--focus", "repeat"] },
  bootstrap: { script: "bootstrap.py" },
  memory: { script: "memory_sync.py" },
  run: { script: "engine_runner.py" },
  doctor: { script: "doctor.py" },
  check: {
    script: "engine_runner.py",
    injectArgs: ["--dry-run", "--steps", "doctor,open,status"],
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
  console.log(`Primary commands:
  chase bootstrap --project <dir> [--force]
  chase doctor --project <dir> [--json]
  chase open --project <dir> [--chapter <n>]
  chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]
  chase write --project <dir> [--chapter <n>] [--steps <csv>]
  chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]
  chase check --project <dir> [--chapter <n>]

Legacy compatibility aliases:
  chase planning --project <dir> [--chapter <n> | --target-chapter <n>]
  chase context --project <dir> [--chapter <n>]
  chase gate --project <dir> [--chapter-no <n>]
  chase draft --project <dir> [--chapter-no <n>]
  chase audit --project <dir> [--chapter-no <n>]
  chase batch --project <dir> [--from <n> --to <n>]
  chase dashboard --project <dir>
  chase foreshadow --project <dir> [--chapter <n>]
  chase arc --project <dir>
  chase timeline --project <dir>
  chase repeat --project <dir>
  chase memory --project <dir> [--chapter <n>]
  chase run --project <dir> [--chapter <n>] [--steps <csv>]

Notes:
  - open is the primary open-book / planning entry; without --chapter it runs launch readiness
  - quality is the unified gate protocol: --check all|chapter|draft|language|batch
  - status is the unified book-health protocol: --focus all|dashboard|foreshadow|arc|timeline|repeat
  - legacy commands are still available, but now route into the new aggregated layers
  - write and check prefer the aggregated layers internally
  - check is a dry-run health sweep over doctor + open + status
  - default run steps: doctor,open,memory,status
  - chase run --chapter expects an already drafted chapter number; do not pass the next unwritten chapter
  - project defaults to the current directory`);
}

main();
