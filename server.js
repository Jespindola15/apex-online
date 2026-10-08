// Servidor de salas para Apex 25: sirve el juego y reenvía el estado entre jugadores.
const http = require('http'), fs = require('fs'), path = require('path');
const { WebSocketServer } = require('ws');
const PORT = process.env.PORT || 3000, MAX = 21;
const html = fs.readFileSync(path.join(__dirname, 'public', 'index.html'));
const rooms = new Map(); // nombre -> Map(id -> {ws, pres})

const srv = http.createServer((q, r) => {
  const u = q.url.split('?')[0];
  if (u === '/' || u === '/index.html') { r.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); r.end(html); }
  else if (u === '/health') { r.writeHead(200); r.end('ok'); }
  else { r.writeHead(404); r.end('No encontrado'); }
});

const wss = new WebSocketServer({ server: srv, path: '/ws', maxPayload: 4096 });
const send = (ws, o) => ws.readyState === 1 && ws.send(JSON.stringify(o));
const others = (R, id, o) => R.forEach((v, k) => k !== id && send(v.ws, o));
// Solo valores simples con claves tipo identificador (el cliente manda x, z, h, lap, etc.)
function clean(d) {
  const o = {}; let n = 0;
  for (const k in d) {
    if (n++ > 24 || !/^[A-Za-z_][A-Za-z0-9_]{0,15}$/.test(k)) continue;
    const v = d[k];
    if (v === null || typeof v === 'boolean' || (typeof v === 'number' && isFinite(v))) o[k] = v;
    else if (typeof v === 'string') o[k] = v.slice(0, 32);
  }
  return o;
}

let seq = 0;
wss.on('connection', ws => {
  const id = (++seq).toString(36) + Math.random().toString(36).slice(2, 6);
  let room = null, R = null, pres = {}, count = 0, win = Date.now();
  ws.alive = true; ws.on('pong', () => ws.alive = true);

  ws.on('message', buf => {
    const now = Date.now(); if (now - win > 1000) { win = now; count = 0; } if (++count > 80) return; // límite de mensajes
    let m; try { m = JSON.parse(buf); } catch { return; }
    if (m.t === 'j' && !room) {
      const name = String(m.r || '').toLowerCase().replace(/[^a-z0-9_.-]/g, '').slice(0, 48);
      if (!name) return;
      R = rooms.get(name) || rooms.set(name, new Map()).get(name);
      if (R.size >= MAX) { send(ws, { t: 'f' }); return ws.close(); }
      room = name; R.set(id, { ws, pres });
      send(ws, { t: 's', me: id, ps: [...R].filter(([k]) => k !== id).map(([k, v]) => ({ id: k, p: v.pres })) });
      others(R, id, { t: 'u', id, d: {} });
    } else if (m.t === 'p' && room && m.d && typeof m.d === 'object') {
      const d = clean(m.d);
      for (const k in d) d[k] === null ? delete pres[k] : (pres[k] = d[k]);
      others(R, id, { t: 'u', id, d });
    }
  });

  ws.on('close', () => {
    if (!room) return;
    R.delete(id); others(R, id, { t: 'l', id });
    if (!R.size) rooms.delete(room);
  });
});

setInterval(() => wss.clients.forEach(ws => { if (!ws.alive) return ws.terminate(); ws.alive = false; ws.ping(); }), 30000);
srv.listen(PORT, () => console.log('Apex 25 online en http://localhost:' + PORT));
