// Kaal VS Code bridge — spawns `kaal --mode rpc` (JSON-RPC over stdio).
// Needs Kaal repo installed + `kaal` on PATH. Untested scaffold (v0.1.0).
const vscode = require('vscode');
const { spawn } = require('child_process');

let proc = null;
let nextId = 0;
const pending = new Map();
let buf = '';

function ensureProc(bin) {
  if (proc && !proc.killed) return proc;
  proc = spawn(bin, ['--mode', 'rpc'], { stdio: ['pipe', 'pipe', 'ignore'] });
  proc.stdout.on('data', (chunk) => {
    buf += chunk.toString();
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line) continue;
      try {
        const res = JSON.parse(line);
        const cb = pending.get(res.id);
        if (cb) { pending.delete(res.id); cb(res); }
      } catch (_) { /* partial line */ }
    }
  });
  proc.on('exit', () => { proc = null; });
  return proc;
}

function rpc(bin, method, params) {
  return new Promise((resolve) => {
    const p = ensureProc(bin);
    const id = ++nextId;
    pending.set(id, resolve);
    p.stdin.write(JSON.stringify({ id, method, params }) + '\n');
    setTimeout(() => { if (pending.has(id)) { pending.delete(id); resolve({ error: 'timeout' }); } }, 120000);
  });
}

function activate(ctx) {
  const bin = () => vscode.workspace.getConfiguration('kaal').get('bin', 'kaal');
  ctx.subscriptions.push(vscode.commands.registerCommand('kaal.runTask', async () => {
    const task = await vscode.window.showInputBox({ prompt: 'Kaal task likho' });
    if (!task) return;
    const res = await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Kaal working…' },
      () => rpc(bin(), 'prompt/run', { task }));
    const out = vscode.window.createOutputChannel('Kaal');
    out.appendLine(JSON.stringify(res.result || res, null, 2));
    out.show(true);
  }));
  ctx.subscriptions.push(vscode.commands.registerCommand('kaal.reviewFile', async () => {
    const f = vscode.window.activeTextEditor?.document.fileName;
    if (!f) { vscode.window.showWarningMessage('Koi file open nahi'); return; }
    const res = await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Kaal reviewing…' },
      () => rpc(bin(), 'prompt/run', { task: `review karo: ${f}` }));
    const out = vscode.window.createOutputChannel('Kaal');
    out.appendLine(JSON.stringify(res.result || res, null, 2));
    out.show(true);
  }));
}

function deactivate() {
  try { if (proc && !proc.killed) proc.kill(); } catch (_) {}
}

module.exports = { activate, deactivate };
