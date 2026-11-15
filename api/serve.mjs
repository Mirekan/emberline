import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const apiDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(apiDir, "..");
const python = path.join(
  root,
  ".venv",
  process.platform === "win32" ? "Scripts" : "bin",
  process.platform === "win32" ? "python.exe" : "python",
);

if (!existsSync(python)) {
  console.error(`Python environment not found at ${python}. Create .venv and install api/requirements.txt first.`);
  process.exit(1);
}

const server = spawn(
  python,
  ["-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8300"],
  { cwd: root, stdio: "inherit" },
);

server.on("error", (error) => {
  console.error("Could not start the EmberLine API:", error.message);
  process.exitCode = 1;
});

server.on("exit", (code) => {
  process.exitCode = code ?? 1;
});
