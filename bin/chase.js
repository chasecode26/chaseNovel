#!/usr/bin/env node
"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

const COMMAND_SPECS = {
  open: { script: "open_book.py" },
  quality: { script: "quality_gate.py" },
  write: { script: "workflow_runner.py" },
  status: { script: "book_health.py" },
  check: {
    script: "workflow_runner.py",
    injectArgs: ["--dry-run", "--steps", "open,quality,status"],
  },
};

const HELP_LINES = [
  "chase open --project <dir> [--chapter <n> | --target-chapter <n>]",
  "chase quality --project <dir> [--chapter-no <n> | --from <n> --to <n>]",
  "chase write --project <dir> [--chapter <n> | --target-chapter <n>] [--steps <csv>]",
  "chase status --project <dir> [--chapter <n>] [--focus <all|dashboard|foreshadow|arc|timeline|repeat>]",
  "chase check --project <dir> [--chapter <n> | --target-chapter <n>]",
];

const NOTE_LINES = [
  "chaseNovel remains the main entry; opening, writer, continue, revise, style, and memory are documentation and contract surfaces",
  "open is the shipped book-opening and next-chapter readiness entry",
  "open treats --chapter as the current reference chapter and defaults target_chapter to reference + 1",
  "write remains the shipped agent writing chain: open,runtime,quality,status",
  "check remains a dry-run sweep: open,quality,status",
  "quality and status stay as shipped governance surfaces",
  "write and check expose both reference chapter and target chapter semantics",
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
