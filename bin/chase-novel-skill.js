#!/usr/bin/env node
"use strict";

const path = require("path");
const { installSkill, doctorSkill, parseArgs } = require("../scripts/install-skill");

async function main() {
  const argv = process.argv.slice(2);
  const { command, options } = parseArgs(argv);
  const repoRoot = path.resolve(__dirname, "..");

  if (command === "install" || command === "update") {
    await installSkill({
      repoRoot,
      targetDir: options.targetDir,
      force: options.force,
    });
    return;
  }

  if (command === "doctor") {
    await doctorSkill({
      repoRoot,
      targetDir: options.targetDir,
    });
    return;
  }

  printHelp();
  process.exitCode = 1;
}

function printHelp() {
  console.log(`Usage:
  npx chase-novel-skill install [--target <dir>] [--force]
  npx chase-novel-skill update [--target <dir>] [--force]
  npx chase-novel-skill doctor [--target <dir>]

Defaults:
  target = ~/.claude/skills/chaseNovel`);
}

main().catch((error) => {
  console.error(`[chase-novel-skill] ${error.message}`);
  process.exit(1);
});
