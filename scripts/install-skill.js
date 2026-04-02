"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");

const REQUIRED_ENTRIES = [
  "hooks",
  "references",
  "scripts",
  "templates",
  "skill.json",
  "SKILL.md",
  "README.md",
];

function defaultTargetDir() {
  return path.join(os.homedir(), ".claude", "skills", "chaseNovel");
}

function parseArgs(argv) {
  const [command = "install", ...rest] = argv;
  const options = {
    targetDir: defaultTargetDir(),
    force: false,
  };

  for (let i = 0; i < rest.length; i += 1) {
    const token = rest[i];
    if (token === "--target") {
      options.targetDir = path.resolve(rest[i + 1]);
      i += 1;
      continue;
    }
    if (token === "--force") {
      options.force = true;
      continue;
    }
    throw new Error(`Unknown option: ${token}`);
  }

  return { command, options };
}

async function installSkill({ repoRoot, targetDir, force }) {
  ensureRepoShape(repoRoot);
  fs.mkdirSync(targetDir, { recursive: true });

  for (const entry of REQUIRED_ENTRIES) {
    const from = path.join(repoRoot, entry);
    const to = path.join(targetDir, entry);
    copyEntry(from, to, force);
  }

  const skillMeta = JSON.parse(fs.readFileSync(path.join(repoRoot, "skill.json"), "utf8"));
  console.log(`[chase-novel-skill] installed ${skillMeta.name}@${skillMeta.version}`);
  console.log(`[chase-novel-skill] target: ${targetDir}`);
}

async function doctorSkill({ repoRoot, targetDir }) {
  ensureRepoShape(repoRoot);

  const missing = [];
  for (const entry of REQUIRED_ENTRIES) {
    const target = path.join(targetDir, entry);
    if (!fs.existsSync(target)) {
      missing.push(entry);
    }
  }

  if (missing.length > 0) {
    console.log("[chase-novel-skill] doctor: missing entries");
    for (const entry of missing) {
      console.log(`- ${entry}`);
    }
    process.exitCode = 2;
    return;
  }

  console.log("[chase-novel-skill] doctor: install looks complete");
  console.log(`[chase-novel-skill] target: ${targetDir}`);
}

function ensureRepoShape(repoRoot) {
  for (const entry of REQUIRED_ENTRIES) {
    const fullPath = path.join(repoRoot, entry);
    if (!fs.existsSync(fullPath)) {
      throw new Error(`Repository is missing required entry: ${entry}`);
    }
  }
}

function copyEntry(from, to, force) {
  const stat = fs.statSync(from);
  if (stat.isDirectory()) {
    copyDirectory(from, to, force);
    return;
  }
  copyFile(from, to, force);
}

function copyDirectory(fromDir, toDir, force) {
  fs.mkdirSync(toDir, { recursive: true });
  for (const name of fs.readdirSync(fromDir)) {
    if (name === "__pycache__") {
      continue;
    }
    copyEntry(path.join(fromDir, name), path.join(toDir, name), force);
  }
}

function copyFile(fromFile, toFile, force) {
  if (!force && fs.existsSync(toFile)) {
    const srcContent = fs.readFileSync(fromFile);
    const dstContent = fs.readFileSync(toFile);
    if (Buffer.compare(srcContent, dstContent) === 0) {
      return;
    }
  }
  fs.mkdirSync(path.dirname(toFile), { recursive: true });
  fs.copyFileSync(fromFile, toFile);
}

module.exports = {
  defaultTargetDir,
  parseArgs,
  installSkill,
  doctorSkill,
};
