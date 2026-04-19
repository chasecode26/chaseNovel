#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const CATEGORY_ORDER = ["code", "docs", "tests", "config", "other"];
const SEARCHABLE_TEXT_EXTENSIONS = new Set([
  ".md",
  ".txt",
  ".json",
  ".yaml",
  ".yml",
  ".toml",
  ".ini",
  ".cfg",
  ".py",
  ".js",
  ".ts",
  ".tsx",
  ".jsx",
  ".go",
  ".rs",
  ".java",
  ".c",
  ".cc",
  ".cpp",
  ".h",
  ".hpp",
  ".sh",
]);
const PYTHON = process.env.PYTHON || "python";
const PYTHON_GIT_BRIDGE = [
  "import json",
  "from pathlib import Path",
  "import subprocess",
  "import sys",
  "result = subprocess.run(['git', *sys.argv[2:]], capture_output=True, text=True)",
  "Path(sys.argv[1]).write_text(json.dumps({'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}), encoding='utf-8')",
].join("; ");

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    printHelp();
    return;
  }

  const repoRoot = resolveRepoRoot();
  const hasHead = gitHasHead(repoRoot);
  const files = collectFiles(repoRoot, options.mode, hasHead);
  const payload = buildPayload(repoRoot, options, files);

  if (options.json) {
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    return;
  }

  printHuman(payload, options.verbose);
}

function parseArgs(argv) {
  const options = {
    mode: "working",
    category: null,
    module: null,
    modulePrefix: null,
    json: false,
    verbose: false,
    summaryOnly: false,
    maxFiles: null,
    topModules: null,
    help: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--mode") {
      const nextToken = argv[index + 1];
      if (!nextToken) {
        fail("missing value for --mode");
      }
      options.mode = nextToken;
      index += 1;
      continue;
    }
    if (token === "--category") {
      const nextToken = argv[index + 1];
      if (!nextToken) {
        fail("missing value for --category");
      }
      options.category = nextToken;
      index += 1;
      continue;
    }
    if (token === "--module") {
      const nextToken = argv[index + 1];
      if (!nextToken) {
        fail("missing value for --module");
      }
      options.module = normalizePath(nextToken);
      index += 1;
      continue;
    }
    if (token === "--module-prefix") {
      const nextToken = argv[index + 1];
      if (!nextToken) {
        fail("missing value for --module-prefix");
      }
      options.modulePrefix = normalizePath(nextToken);
      index += 1;
      continue;
    }
    if (token === "--json") {
      options.json = true;
      continue;
    }
    if (token === "--summary-only") {
      options.summaryOnly = true;
      continue;
    }
    if (token === "--max-files") {
      const nextToken = argv[index + 1];
      if (!nextToken) {
        fail("missing value for --max-files");
      }
      const parsed = Number(nextToken);
      if (!Number.isInteger(parsed) || parsed < 0) {
        fail(`invalid value for --max-files: ${nextToken}`);
      }
      options.maxFiles = parsed;
      index += 1;
      continue;
    }
    if (token === "--top-modules") {
      const nextToken = argv[index + 1];
      if (!nextToken) {
        fail("missing value for --top-modules");
      }
      const parsed = Number(nextToken);
      if (!Number.isInteger(parsed) || parsed < 0) {
        fail(`invalid value for --top-modules: ${nextToken}`);
      }
      options.topModules = parsed;
      index += 1;
      continue;
    }
    if (token === "-v" || token === "--verbose") {
      options.verbose = true;
      continue;
    }
    if (token === "-h" || token === "--help" || token === "help") {
      options.help = true;
      continue;
    }
    fail(`unknown argument: ${token}`);
  }

  if (!["working", "staged", "committed"].includes(options.mode)) {
    fail(`unsupported mode: ${options.mode}`);
  }
  if (options.category !== null && !CATEGORY_ORDER.includes(options.category)) {
    fail(`unsupported category: ${options.category}`);
  }

  return options;
}

function resolveRepoRoot() {
  const repoRoot = runGit(["rev-parse", "--show-toplevel"], process.cwd()).trim();
  if (!repoRoot) {
    throw new Error("unable to resolve git repo root");
  }
  return repoRoot;
}

function gitHasHead(repoRoot) {
  const result = runGitAllowFailure(["rev-parse", "--verify", "HEAD"], repoRoot);
  return result.status === 0;
}

function collectFiles(repoRoot, mode, hasHead) {
  const statusMap = new Map();
  const numstatMap = new Map();

  for (const entry of readNameStatusEntries(repoRoot, mode, hasHead)) {
    statusMap.set(entry.path, {
      path: entry.path,
      status: entry.status,
      previousPath: entry.previousPath || null,
    });
  }

  for (const entry of readNumstatEntries(repoRoot, mode, hasHead)) {
    numstatMap.set(entry.path, entry);
  }

  for (const entry of readUntrackedEntries(repoRoot, mode)) {
    statusMap.set(entry.path, {
      path: entry.path,
      status: entry.status,
      previousPath: null,
    });
    if (!numstatMap.has(entry.path)) {
      numstatMap.set(entry.path, {
        path: entry.path,
        added: countFileLines(path.join(repoRoot, entry.path)),
        deleted: 0,
      });
    }
  }

  const paths = new Set([...statusMap.keys(), ...numstatMap.keys()]);
  const files = [];
  for (const filePath of paths) {
    const normalizedPath = normalizePath(filePath);
    if (shouldIgnorePath(normalizedPath)) {
      continue;
    }
    const statusInfo = statusMap.get(filePath) || { status: "M", previousPath: null };
    const lineInfo = numstatMap.get(filePath) || { added: 0, deleted: 0 };
    const category = classifyPath(normalizedPath);
    files.push({
      path: normalizedPath,
      status: statusInfo.status,
      previous_path: statusInfo.previousPath ? normalizePath(statusInfo.previousPath) : null,
      category,
      module: detectModule(normalizedPath),
      added: lineInfo.added,
      deleted: lineInfo.deleted,
    });
  }

  files.sort((left, right) => left.path.localeCompare(right.path));
  return files;
}

function readNameStatusEntries(repoRoot, mode, hasHead) {
  const output = runGit(buildNameStatusCommand(mode, hasHead), repoRoot);
  return output
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseNameStatusLine)
    .filter(Boolean);
}

function readNumstatEntries(repoRoot, mode, hasHead) {
  const output = runGit(buildNumstatCommand(mode, hasHead), repoRoot);
  return output
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseNumstatLine)
    .filter(Boolean);
}

function readUntrackedEntries(repoRoot, mode) {
  if (mode !== "working") {
    return [];
  }
  const output = runGit(["ls-files", "--others", "--exclude-standard"], repoRoot);
  return output
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((filePath) => ({ path: filePath, status: "A" }));
}

function buildNameStatusCommand(mode, hasHead) {
  if (mode === "staged") {
    return ["diff", "--cached", "--name-status", "--find-renames"];
  }
  if (mode === "committed") {
    return hasHead
      ? ["show", "--name-status", "--format=", "--find-renames", "HEAD"]
      : ["diff", "--name-status", "--find-renames"];
  }
  if (hasHead) {
    return ["diff", "--name-status", "--find-renames", "HEAD", "--"];
  }
  return ["diff", "--cached", "--name-status", "--find-renames"];
}

function buildNumstatCommand(mode, hasHead) {
  if (mode === "staged") {
    return ["diff", "--cached", "--numstat", "--find-renames"];
  }
  if (mode === "committed") {
    return hasHead
      ? ["show", "--numstat", "--format=", "--find-renames", "HEAD"]
      : ["diff", "--cached", "--numstat", "--find-renames"];
  }
  if (hasHead) {
    return ["diff", "--numstat", "--find-renames", "HEAD", "--"];
  }
  return ["diff", "--cached", "--numstat", "--find-renames"];
}

function parseNameStatusLine(line) {
  const parts = line.split("\t");
  if (parts.length < 2) {
    return null;
  }
  const rawStatus = parts[0];
  const status = rawStatus.startsWith("R") ? "R" : rawStatus.startsWith("C") ? "C" : rawStatus;
  if ((status === "R" || status === "C") && parts.length >= 3) {
    return {
      status,
      previousPath: parts[1],
      path: parts[2],
    };
  }
  return {
    status,
    previousPath: null,
    path: parts[1],
  };
}

function parseNumstatLine(line) {
  const parts = line.split("\t");
  if (parts.length < 3) {
    return null;
  }
  return {
    added: parseNumstatValue(parts[0]),
    deleted: parseNumstatValue(parts[1]),
    path: parts.slice(2).join("\t"),
  };
}

function parseNumstatValue(value) {
  return /^\d+$/.test(value) ? Number(value) : 0;
}

function countFileLines(filePath) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    if (!content) {
      return 0;
    }
    return content.split(/\r?\n/).length;
  } catch (error) {
    return 0;
  }
}

function classifyPath(filePath) {
  const normalized = normalizePath(filePath);
  const basename = path.posix.basename(normalized).toLowerCase();
  const extension = path.posix.extname(normalized).toLowerCase();

  if (
    normalized.startsWith("tests/") ||
    normalized.includes("/tests/") ||
    normalized.includes("/__tests__/") ||
    /\.test\./.test(normalized) ||
    /\.spec\./.test(normalized) ||
    basename === "smoke_check.py"
  ) {
    return "tests";
  }

  if (
    normalized.startsWith("docs/") ||
    normalized.startsWith("references/") ||
    normalized.startsWith("templates/") ||
    basename === "readme.md" ||
    basename === "architecture.md" ||
    basename === "skill.md" ||
    extension === ".md"
  ) {
    return "docs";
  }

  if (
    basename === "package.json" ||
    basename === "package-lock.json" ||
    basename === "pnpm-lock.yaml" ||
    basename === "pyproject.toml" ||
    basename === "requirements.txt" ||
    normalized.startsWith("schemas/") ||
    normalized.startsWith(".github/") ||
    [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"].includes(extension)
  ) {
    return "config";
  }

  if (
    normalized.startsWith("scripts/") ||
    normalized.startsWith("runtime/") ||
    normalized.startsWith("evaluators/") ||
    normalized.startsWith("bin/") ||
    [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".cc", ".cpp", ".h", ".hpp"].includes(extension)
  ) {
    return "code";
  }

  return "other";
}

function shouldIgnorePath(filePath) {
  const normalized = normalizePath(filePath);
  const basename = path.posix.basename(normalized).toLowerCase();
  return (
    normalized.startsWith(".tmp-") ||
    normalized.includes("/.tmp-") ||
    normalized.startsWith("04_gate/") ||
    normalized.startsWith("05_reports/") ||
    normalized.startsWith("00_memory/retrieval/") ||
    basename === "commit_message.txt" ||
    normalized.includes("/__pycache__/") ||
    normalized.endsWith(".pyc") ||
    normalized.endsWith(".tgz")
  );
}

function detectModule(filePath) {
  const normalized = normalizePath(filePath);
  const parts = normalized.split("/");
  if (parts.length <= 1) {
    return "root";
  }
  if (["docs", "references", "templates", "assets"].includes(parts[0])) {
    if (parts.length === 2) {
      return parts[0];
    }
    return `${parts[0]}/${parts[1]}`;
  }
  return parts[0];
}

function buildPayload(repoRoot, options, files) {
  const globalModules = summarizeModules(files);
  const globalSummary = summarizeFiles(files, globalModules);
  const globalDeletedReferenceHits = findDeletedReferenceHits(repoRoot, files);
  const filteredFiles = filterFiles(files, options);
  const modules = summarizeModules(filteredFiles);
  const summary = summarizeFiles(filteredFiles, modules);
  const deletedReferenceHits = filterDeletedReferenceHits(globalDeletedReferenceHits, filteredFiles);
  const visibleFiles = selectVisibleFiles(filteredFiles, options);
  const visibleModules = selectVisibleModules(modules, options.topModules);
  const omittedFileCount = Math.max(0, filteredFiles.length - visibleFiles.length);
  const omittedModuleCount = Math.max(0, modules.length - visibleModules.length);
  return {
    status: filteredFiles.length === 0 ? "clean" : "ok",
    generated_at: new Date().toISOString(),
    mode: options.mode,
    selected_category: options.category,
    selected_module: options.module,
    selected_module_prefix: options.modulePrefix,
    repo_root: normalizePath(repoRoot),
    global_summary: globalSummary,
    summary,
    modules: visibleModules,
    global_deleted_reference_hits: globalDeletedReferenceHits,
    deleted_reference_hits: deletedReferenceHits,
    global_warnings: buildWarnings(files, globalSummary, globalDeletedReferenceHits),
    warnings: buildWarnings(filteredFiles, summary, deletedReferenceHits),
    global_recommendations: buildRecommendations(files, globalSummary, globalDeletedReferenceHits),
    recommendations: buildRecommendations(filteredFiles, summary, deletedReferenceHits),
    module_list_truncated: omittedModuleCount > 0,
    shown_module_count: visibleModules.length,
    omitted_module_count: omittedModuleCount,
    module_limit: options.topModules,
    file_list_truncated: omittedFileCount > 0,
    shown_file_count: visibleFiles.length,
    omitted_file_count: omittedFileCount,
    file_limit: options.summaryOnly ? 0 : options.maxFiles,
    files: visibleFiles,
  };
}

function filterFiles(files, options) {
  let filteredFiles = files;
  if (options.category !== null) {
    filteredFiles = filteredFiles.filter((file) => file.category === options.category);
  }
  if (options.module !== null) {
    filteredFiles = filteredFiles.filter((file) => file.module === options.module);
  }
  if (options.modulePrefix !== null) {
    filteredFiles = filteredFiles.filter((file) => file.module === options.modulePrefix || file.module.startsWith(`${options.modulePrefix}/`));
  }
  return filteredFiles;
}

function selectVisibleFiles(files, options) {
  if (options.summaryOnly) {
    return [];
  }
  if (options.maxFiles === null) {
    return files;
  }
  return files.slice(0, options.maxFiles);
}

function selectVisibleModules(modules, topModules) {
  if (topModules === null) {
    return modules;
  }
  return modules.slice(0, topModules);
}

function summarizeFiles(files, modules = null) {
  const categoryCounts = Object.fromEntries(CATEGORY_ORDER.map((name) => [name, 0]));
  const statusCounts = {};
  let addedLines = 0;
  let deletedLines = 0;
  let codeChangeLines = 0;
  let addedFiles = 0;
  let deletedFiles = 0;
  let renamedFiles = 0;

  for (const file of files) {
    categoryCounts[file.category] = (categoryCounts[file.category] || 0) + 1;
    statusCounts[file.status] = (statusCounts[file.status] || 0) + 1;
    addedLines += file.added;
    deletedLines += file.deleted;
    if (file.category === "code") {
      codeChangeLines += file.added + file.deleted;
    }
    if (file.status === "A") {
      addedFiles += 1;
    }
    if (file.status === "D") {
      deletedFiles += 1;
    }
    if (file.status === "R") {
      renamedFiles += 1;
    }
  }

  return {
    changed_files: files.length,
    added_lines: addedLines,
    deleted_lines: deletedLines,
    code_change_lines: codeChangeLines,
    added_files: addedFiles,
    deleted_files: deletedFiles,
    renamed_files: renamedFiles,
    category_counts: categoryCounts,
    status_counts: statusCounts,
    module_count: modules ? modules.length : summarizeModules(files).length,
  };
}

function summarizeModules(files) {
  const moduleMap = new Map();
  for (const file of files) {
    const current = moduleMap.get(file.module) || {
      name: file.module,
      file_count: 0,
      categories: {},
    };
    current.file_count += 1;
    current.categories[file.category] = (current.categories[file.category] || 0) + 1;
    moduleMap.set(file.module, current);
  }

  return [...moduleMap.values()].sort((left, right) => {
    if (right.file_count !== left.file_count) {
      return right.file_count - left.file_count;
    }
    return left.name.localeCompare(right.name);
  });
}

function buildWarnings(files, summary, deletedReferenceHits = []) {
  const warnings = [];
  const docsTouched = files.some((file) => file.category === "docs");
  const testsTouched = files.some((file) => file.category === "tests");
  const readmeTouched = files.some((file) => path.posix.basename(file.path).toLowerCase() === "readme.md");
  const configTouched = files.some((file) => file.category === "config");
  const deletedTouched = files.some((file) => file.status === "D");

  if (summary.code_change_lines > 50 && !docsTouched) {
    warnings.push("代码改动已超过 50 行，但本轮未见文档同步。");
  }
  if (summary.code_change_lines > 30 && !testsTouched) {
    warnings.push("代码改动已超过 30 行，但本轮未见测试或 smoke 侧同步。");
  }
  if (summary.added_files > 0 && !readmeTouched) {
    warnings.push("本轮新增了文件，但未见 README 同步入口说明。");
  }
  if (configTouched && !docsTouched) {
    warnings.push("本轮存在配置/schema 变化，但未见配套文档说明。");
  }
  if (deletedTouched) {
    warnings.push("本轮存在删除文件，请确认所有入口、引用和兼容说明已清理。");
  }

  if (deletedReferenceHits.length > 0) {
    warnings.push(`detected ${deletedReferenceHits.length} deleted files that are still referenced in the current repo`);
  }

  return warnings;
}

function buildRecommendations(files, summary, deletedReferenceHits = []) {
  const recommendations = [];
  if (summary.changed_files === 0) {
    recommendations.push("当前工作树没有待分析变更。");
    return recommendations;
  }
  if (summary.code_change_lines > 0) {
    recommendations.push("优先复核 runtime / workflow / smoke 是否仍沿用同一章节语义。");
  }
  if (files.some((file) => file.category === "docs")) {
    recommendations.push("确认 docs/core 与 README 是否只保留当前主入口口径。");
  }
  if (files.some((file) => file.status === "D")) {
    recommendations.push("逐个删除文件检查旧命令、模板和打包清单是否还有残留引用。");
  }
  if (deletedReferenceHits.length > 0) {
    recommendations.push("clear deleted_reference_hits before closing this cleanup round");
  }
  return recommendations;
}

function printHuman(payload, verbose) {
  const { summary } = payload;
  console.log(`mode=${payload.mode}`);
  console.log(`category=${payload.selected_category || "all"}`);
  console.log(`module=${payload.selected_module || "all"}`);
  console.log(`module_prefix=${payload.selected_module_prefix || "all"}`);
  console.log(`status=${payload.status}`);
  console.log(
    `files=${summary.changed_files} lines=+${summary.added_lines}/-${summary.deleted_lines} code_lines=${summary.code_change_lines}`
  );
  console.log(
    `categories=${CATEGORY_ORDER.map((name) => `${name}:${summary.category_counts[name] || 0}`).join(" ")}`
  );
  console.log(`modules=${payload.modules.map((item) => `${item.name}:${item.file_count}`).join(", ") || "none"}`);

  if (payload.module_list_truncated) {
    console.log(
      `modules_shown=${payload.shown_module_count} omitted=${payload.omitted_module_count} limit=${payload.module_limit === null ? "all" : payload.module_limit}`
    );
  }

  if (payload.warnings.length) {
    console.log("warnings:");
    for (const warning of payload.warnings) {
      console.log(`- ${warning}`);
    }
  }

  if (
    (payload.selected_category !== null || payload.selected_module !== null || payload.selected_module_prefix !== null) &&
    payload.global_warnings.length
  ) {
    console.log("global_warnings:");
    for (const warning of payload.global_warnings) {
      console.log(`- ${warning}`);
    }
  }

  if (payload.recommendations.length) {
    console.log("recommendations:");
    for (const recommendation of payload.recommendations) {
      console.log(`- ${recommendation}`);
    }
  }

  if (
    (payload.selected_category !== null || payload.selected_module !== null || payload.selected_module_prefix !== null) &&
    payload.global_recommendations.length
  ) {
    console.log("global_recommendations:");
    for (const recommendation of payload.global_recommendations) {
      console.log(`- ${recommendation}`);
    }
  }

  if (payload.file_list_truncated) {
    console.log(
      `files_shown=${payload.shown_file_count} omitted=${payload.omitted_file_count} limit=${payload.file_limit === null ? "all" : payload.file_limit}`
    );
  }

  if (payload.deleted_reference_hits.length) {
    console.log("deleted_reference_hits:");
    for (const hit of payload.deleted_reference_hits) {
      const references = hit.references.map((item) => `${item.path}:${item.matches}`).join(", ");
      console.log(`- ${hit.deleted_path} <- ${references}`);
    }
  }

  if (verbose) {
    console.log("files:");
    for (const file of payload.files) {
      const renameNote = file.previous_path ? ` <- ${file.previous_path}` : "";
      console.log(
        `- [${file.status}] ${file.path} category=${file.category} module=${file.module} +${file.added}/-${file.deleted}${renameNote}`
      );
    }
  }
}

function printHelp() {
  console.log(`Usage:
  node scripts/change_analyzer.js [--mode working|staged|committed] [--category <${CATEGORY_ORDER.join("|")}>] [--module <name>] [--module-prefix <prefix>] [--json] [--summary-only] [--max-files <n>] [--top-modules <n>] [-v]

Options:
  --mode   working (default), staged, committed
  --category     limit output to one category view: ${CATEGORY_ORDER.join(", ")}
  --module       limit output to one detected module bucket, for example scripts or docs/core
  --module-prefix  limit output to one module family, for example docs or references
  --json   emit machine-readable JSON
  --summary-only  omit per-file entries and return summary/module data only
  --max-files     limit returned file entries to the first N after sorting
  --top-modules   limit returned module entries to the top N after sorting
  -v       include per-file breakdown in human output
  -h       show this help`);
}

function findDeletedReferenceHits(repoRoot, files) {
  const deletedFiles = files.filter((file) => file.status === "D");
  if (deletedFiles.length === 0) {
    return [];
  }

  const textFiles = collectSearchableFiles(repoRoot);
  const hitsByDeletedPath = new Map(
    deletedFiles.map((file) => [
      file.path,
      {
        deleted_path: file.path,
        deleted_module: file.module,
        references: [],
      },
    ])
  );

  for (const absolutePath of textFiles) {
    const relativePath = normalizePath(path.relative(repoRoot, absolutePath));
    if (!relativePath || shouldIgnorePath(relativePath)) {
      continue;
    }
    let content = "";
    try {
      content = fs.readFileSync(absolutePath, "utf8");
    } catch (error) {
      continue;
    }
    for (const deletedFile of deletedFiles) {
      const matches = countOccurrences(content, deletedFile.path);
      if (matches <= 0) {
        continue;
      }
      hitsByDeletedPath.get(deletedFile.path).references.push({
        path: relativePath,
        matches,
      });
    }
  }

  return [...hitsByDeletedPath.values()]
    .filter((item) => item.references.length > 0)
    .map((item) => ({
      ...item,
      references: item.references.sort((left, right) => {
        if (right.matches !== left.matches) {
          return right.matches - left.matches;
        }
        return left.path.localeCompare(right.path);
      }),
    }))
    .sort((left, right) => left.deleted_path.localeCompare(right.deleted_path));
}

function filterDeletedReferenceHits(globalHits, filteredFiles) {
  const deletedPaths = new Set(filteredFiles.filter((file) => file.status === "D").map((file) => file.path));
  if (deletedPaths.size === 0) {
    return [];
  }
  return globalHits.filter((item) => deletedPaths.has(item.deleted_path));
}

function collectSearchableFiles(rootDir) {
  const results = [];
  walkDirectory(rootDir, rootDir, results);
  return results;
}

function walkDirectory(rootDir, currentDir, results) {
  let entries = [];
  try {
    entries = fs.readdirSync(currentDir, { withFileTypes: true });
  } catch (error) {
    return;
  }

  for (const entry of entries) {
    if (entry.name === ".git" || entry.name === "node_modules") {
      continue;
    }
    const absolutePath = path.join(currentDir, entry.name);
    const relativePath = normalizePath(path.relative(rootDir, absolutePath));
    if (relativePath && shouldIgnorePath(relativePath)) {
      continue;
    }
    if (entry.isDirectory()) {
      walkDirectory(rootDir, absolutePath, results);
      continue;
    }
    if (!entry.isFile() || !isSearchableTextFile(absolutePath)) {
      continue;
    }
    results.push(absolutePath);
  }
}

function isSearchableTextFile(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  if (SEARCHABLE_TEXT_EXTENSIONS.has(extension)) {
    return true;
  }
  const basename = path.basename(filePath).toLowerCase();
  return basename === "readme.md" || basename === "architecture.md" || basename === "skill.md";
}

function countOccurrences(content, needle) {
  if (!needle) {
    return 0;
  }
  let count = 0;
  let offset = 0;
  while (offset < content.length) {
    const index = content.indexOf(needle, offset);
    if (index < 0) {
      break;
    }
    count += 1;
    offset = index + needle.length;
  }
  return count;
}

function runGit(args, cwd) {
  const result = runGitAllowFailure(args, cwd);
  if (result.status !== 0) {
    const message = (result.stderr || result.stdout || "").trim() || "git command failed";
    throw new Error(message);
  }
  return result.stdout;
}

function runGitAllowFailure(args, cwd) {
  const tempDir = fs.mkdtempSync(path.join(cwd, ".tmp-change-analyzer-"));
  const outputPath = path.join(tempDir, "git-result.json");
  const result = spawnSync(PYTHON, ["-c", PYTHON_GIT_BRIDGE, outputPath, ...args], {
    cwd,
    stdio: "inherit",
    windowsHide: true,
  });
  let payload = null;
  try {
    payload = JSON.parse(fs.readFileSync(outputPath, "utf8"));
  } catch (error) {
    payload = null;
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
  if (result.error) {
    return {
      status: 1,
      stdout: "",
      stderr: String(result.error.message || result.error),
    };
  }
  if (result.status !== 0 && !payload) {
    return {
      status: result.status || 1,
      stdout: "",
      stderr: "",
    };
  }
  return {
    status: payload ? Number(payload.returncode || 0) : result.status || 0,
    stdout: payload ? String(payload.stdout || "") : result.stdout || "",
    stderr: payload ? String(payload.stderr || "") : result.stderr || "",
  };
}

function normalizePath(value) {
  return String(value).replace(/\\/g, "/");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

main();
