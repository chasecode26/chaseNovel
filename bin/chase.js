#!/usr/bin/env node
"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

const COMMAND_SPECS = {
  open: { script: "open_book.py" },
  quality: { script: "quality_gate.py" },
  write: { script: "workflow_runner.py" },
  status: { script: "book_health.py" },
  bootstrap: { script: "project_bootstrap.py" },
  doctor: { script: "project_doctor.py" },
  check: {
    script: "workflow_runner.py",
    injectArgs: ["--dry-run", "--steps", "doctor,open,quality,status"],
  },
};

const HELP_LINES = [
  "chase bootstrap --project <dir> [--force]",
  "chase doctor --project <dir> [--json]",
  "chase open --project <dir> [--chapter <n> | --target-chapter <n>]",
  "chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]",
  "chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]",
  "chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]",
  "chase check --project <dir> [--chapter <n> | --target-chapter <n>]",
];

const NOTE_LINES = [
  "open is the primary open-book and next-chapter planning entry",
  "open uses --chapter as the current drafted reference chapter and defaults to target_chapter = reference + 1; use --target-chapter to override",
  "quality is the unified gate protocol: --check all|chapter|draft|language|batch",
  "status is the unified book-health protocol: --focus all|dashboard|foreshadow|arc|timeline|repeat",
  "write/check expose both reference chapter and target chapter semantics",
  "check is a dry-run health sweep over doctor + open + quality + status",
  "write default steps: doctor,open,runtime,quality,status",
  "project defaults to the current directory",
];

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
  const sections = [
    "Commands:",
    ...HELP_LINES.map((line) => `  ${line}`),
    "",
    "Notes:",
    ...NOTE_LINES.map((line) => `  - ${line}`),
  ];
  console.log(sections.join("\n"));
}

main();
