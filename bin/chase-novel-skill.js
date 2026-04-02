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

Local workflow:
  npx chase context --project <dir> [--chapter <n>]
  npx chase foreshadow --project <dir> [--chapter <n>]
  npx chase dashboard --project <dir>
  npx chase arc --project <dir>
  npx chase timeline --project <dir>
  npx chase repeat --project <dir>
  npx chase memory --project <dir> [--chapter <n>]
  npx chase gate --project <dir> [--chapter-no <n>]
  npx chase batch --project <dir> [--from <n> --to <n>]
  npx chase bootstrap --project <dir> [--force]
  npx chase run --project <dir> [--chapter <n>] [--steps <csv>]

Defaults:
  target = ~/.claude/skills/chaseNovel`);
}

main().catch((error) => {
  console.error(`[chase-novel-skill] ${error.message}`);
  process.exit(1);
});
