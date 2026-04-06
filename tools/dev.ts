import { createServer } from "node:net";
import { spawnBackend } from "./run-backend.ts";

const cwd = process.cwd();

function isPortAvailable(port: number): Promise<boolean> {
  return new Promise(resolve => {
    const server = createServer();

    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close(() => resolve(true));
    });

    server.listen(port, "127.0.0.1");
  });
}

async function pickFrontendPort(): Promise<number> {
  const requested = Number(process.env.PORT ?? "3000");

  if (Number.isNaN(requested) || requested <= 0) {
    return 3000;
  }

  if (await isPortAvailable(requested)) {
    return requested;
  }

  const fallback = requested + 1;
  if (await isPortAvailable(fallback)) {
    console.warn(`Port ${requested} is in use, using ${fallback} for frontend.`);
    return fallback;
  }

  throw new Error(`Frontend ports ${requested} and ${fallback} are both in use.`);
}

const frontendPort = await pickFrontendPort();

const client = Bun.spawn({
  cmd: ["bun", "--hot", "src/index.ts"],
  cwd,
  stdout: "inherit",
  stderr: "inherit",
  stdin: "inherit",
  env: {
    ...process.env,
    PORT: String(frontendPort),
    HOST: process.env.HOST ?? "127.0.0.1",
  },
});

const backend = spawnBackend();

let shuttingDown = false;

function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;

  client.kill();
  backend.kill();

  setTimeout(() => process.exit(code), 50);
}

for (const sig of ["SIGINT", "SIGTERM"] as const) {
  process.on(sig, () => shutdown(0));
}

void Promise.race([
  client.exited.then((code: number | null) => {
    console.error(`Client process exited (${code}).`);
    shutdown(code ?? 1);
  }),
  backend.exited.then((code: number | null) => {
    console.error(`Backend process exited (${code}).`);
    shutdown(code ?? 1);
  }),
]);
