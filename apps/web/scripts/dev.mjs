import { rmSync } from "node:fs";
import { spawn } from "node:child_process";

// Next dev occasionally reuses an incomplete `.next` server bundle and
// crashes on auth routes with missing vendor chunks. Start from a clean cache.
rmSync(new URL("../.next", import.meta.url), { force: true, recursive: true });

const child = spawn("next", ["dev"], {
  env: process.env,
  shell: process.platform === "win32",
  stdio: "inherit"
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 0);
});
