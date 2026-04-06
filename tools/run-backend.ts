import { existsSync } from "node:fs";
import { join } from "node:path";

const cwd = process.cwd();
const backendScript = join(cwd, "backend", "chad_rag_backend.py");

function spawnOrThrow(cmd: string[]) {
  return Bun.spawn({
    cmd,
    cwd,
    stdout: "inherit",
    stderr: "inherit",
    stdin: "inherit",
  });
}

function backendCandidates(): string[][] {
  const windowsVenvs = [
    join(cwd, "backend", "venv", "Scripts", "python.exe"),
    join(cwd, "backend", ".venv", "Scripts", "python.exe"),
  ].filter(existsSync);

  const unixVenvs = [
    join(cwd, "backend", "venv", "bin", "python"),
    join(cwd, "backend", ".venv", "bin", "python"),
  ].filter(existsSync);

  return [
    ...windowsVenvs.map(python => [python, backendScript]),
    ...unixVenvs.map(python => [python, backendScript]),
    ["bash", "backend/run_server.sh"],
    ["py", "-3", backendScript],
    ["python3", backendScript],
    ["python", backendScript],
  ];
}

export function spawnBackend() {
  for (const cmd of backendCandidates()) {
    try {
      return spawnOrThrow(cmd);
    } catch {
      // Try next backend command candidate.
    }
  }

  throw new Error("Could not start backend. Install Python 3 and backend requirements.");
}

if (import.meta.main) {
  const backend = spawnBackend();
  const code = await backend.exited;
  process.exit(code ?? 1);
}
