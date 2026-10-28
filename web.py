"""TasteTruce local web UI: no secret ever reaches browser. Python stdlib only."""
import argparse
import json
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from tastetruce import plan, QlooError

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TasteTruce • Find common ground</title>
<style>
:root{color-scheme:dark;font:16px/1.5 system-ui,Segoe UI,sans-serif;background:#091321;color:#f0f4ff}*{box-sizing:border-box}body{margin:0}main{max-width:900px;margin:56px auto;padding:0 24px}h1{font-size:clamp(2.4rem,6vw,4.8rem);letter-spacing:-.055em;line-height:1.04;margin:0 0 12px}.sub{color:#aabbd5;font-size:1.12rem;max-width:620px}.eyebrow{color:#6ee7ba;font-weight:800;letter-spacing:.18em;text-transform:uppercase;font-size:.75rem}.panel{background:#142237;border:1px solid #30425f;border-radius:20px;padding:24px;margin-top:28px}label{font-weight:700;display:block;margin:14px 0 6px}input{width:100%;border-radius:10px;border:1px solid #526582;background:#0b1729;padding:13px;color:white;font:inherit}button{background:#74eab6;color:#09231b;border:none;border-radius:12px;padding:15px 23px;cursor:pointer;font-weight:800;font-size:1rem;margin-top:18px}button:disabled{opacity:.6;cursor:wait}small{color:#9fb0c7}.chips{display:flex;gap:10px;flex-wrap:wrap}.chip{background:#243b52;padding:5px 12px;border-radius:22px;font-size:.85rem}.results{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px;margin:24px 0}.pick{background:#18304a;padding:20px;border-radius:14px;border:1px solid #345575}.pick h3{margin:4px 0}.pick p{color:#bdd0df;font-size:.9rem}.error{color:#ffa8aa}footer{color:#8194ad;font-size:.8rem;margin:48px 0}</style></head>
<body><main><p class="eyebrow">Cultural intelligence × fairness</p><h1>Good taste.<br>Common ground.</h1><p class="sub">Two people, different tastes. TasteTruce searches Qloo's cultural graph for things both people might genuinely enjoy, rather than optimizing only for the average.</p>
<div class="panel"><div class="chips"><span class="chip">Cross-domain discovery</span><span class="chip">Fairness first</span><span class="chip">Evidence-based picks</span></div>
<label for="a">Person A: favorite artist</label><input id="a" value="Radiohead" maxlength="100">
<label for="b">Person B: favorite artist</label><input id="b" value="Daft Punk" maxlength="100">
<label for="loc">City for dining picks (optional)</label><input id="loc" value="New York" maxlength="100">
<button id="go">Find common ground →</button><p><small id="mode"></small></p></div><div id="out" aria-live="polite"></div>
<footer>Qloo Agentic Hackathon 2026 • Live recommendations only when the server has a valid API key. Offline fixture responses are conspicuously marked.</footer></main>
<script>
const out=document.getElementById('out'),btn=document.getElementById('go');
async function run(){btn.disabled=true;out.textContent='Consulting cultural taste graph…';try{
 const body={profiles:[[document.getElementById('a').value],[document.getElementById('b').value]],location:document.getElementById('loc').value||null};
 const res=await fetch('/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const data=await res.json();if(!res.ok)throw Error(data.error||'Request failed');
 document.getElementById('mode').textContent=data.mode;
 out.replaceChildren();const title=document.createElement('h2');title.textContent=data.mode.startsWith('OFFLINE')?'DEMO FIXTURES — NOT REAL QLOO RESULTS':'Live Qloo recommendations';out.append(title);
 const grid=document.createElement('div');grid.className='results';
 for(const item of data.choices){const card=document.createElement('div');card.className='pick';const category=document.createElement('small');category.textContent=item.category.toUpperCase();const name=document.createElement('h3');name.textContent=item.name||'No common match';const why=document.createElement('p');why.textContent=item.why;card.append(category,name,why);if(Array.isArray(item.participant_affinities)&&item.participant_affinities.length){const details=document.createElement('p');details.textContent='Evidence: '+item.participant_affinities.map((v,i)=>'Person '+(i+1)+': '+Number(v).toFixed(3)).join(' • ')+'. Fairness score weights the least-matched person most heavily.';card.append(details)}if(Array.isArray(item.participant_ranks)&&item.participant_ranks.length){const ranks=document.createElement('small');ranks.textContent='Qloo result position: '+item.participant_ranks.map((v,i)=>'Person '+(i+1)+' #'+v).join(' • ');card.append(ranks)}if(item.score!==null&&item.score!==undefined){const evidence=document.createElement('small');evidence.textContent='Consensus score: '+Number(item.score).toFixed(3)+' • Source: '+String(item.source||'unknown');card.append(evidence)}grid.append(card)}out.append(grid);
 if(data.unresolved?.length){const note=document.createElement('p');note.textContent='Unresolved interests: '+data.unresolved.map(x=>x.interest).join(', ');out.append(note)}
 }catch(err){out.textContent='';const p=document.createElement('p');p.className='error';p.textContent=err.message;out.append(p)}finally{btn.disabled=false}}
btn.addEventListener('click',run);
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    rate_lock = threading.Lock()
    requests_by_ip = {}
    requests_total = 0
    max_live_requests = int(os.environ.get('QLOO_MAX_LIVE_REQUESTS', '100'))
    min_interval_seconds = 30

    def allow_live_request(self):
        if self.offline:
            return True
        # Trust socket address rather than user-controlled X-Forwarded-For.
        ip = self.client_address[0]
        now = time.monotonic()
        with self.rate_lock:
            if self.requests_total >= self.max_live_requests:
                return False
            if now - self.requests_by_ip.get(ip, -1e12) < self.min_interval_seconds:
                return False
            self.requests_by_ip[ip] = now
            self.__class__.requests_total += 1
        return True

    offline = True
    def do_HEAD(self):
        if urlsplit(self.path).path in ("/", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if urlsplit(self.path).path == "/healthz":
            return self.reply(200, {"status": "ok", "mode": "OFFLINE_FIXTURE" if self.offline else "LIVE_QLOO"})
        if urlsplit(self.path).path != "/":
            return self.reply(404, {"error": "Not found"})
        payload = HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/plan":
            return self.reply(404, {"error": "Not found"})
        if not self.allow_live_request():
            return self.reply(429, {"error": "Live Qloo request quota reached. Try again later."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2048:
                return self.reply(413, {"error": "Invalid payload size"})
            args = json.loads(self.rfile.read(length))
            result = plan(args["profiles"], location=args.get("location"),
                          offline=self.offline)
            self.reply(200, result)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self.reply(400, {"error": "Invalid input: " + str(exc)})
        except QlooError as exc:
            self.reply(502, {"error": str(exc)})
    def reply(self, status, data):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use server-side QLOO_API_KEY")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    if args.live and not os.environ.get("QLOO_API_KEY"):
        parser.error("QLOO_API_KEY must be set on server")
    # Render auto-enables live mode only when its server-side key is configured.
    Handler.offline = not (args.live or bool(os.environ.get("QLOO_API_KEY")))
    print("TasteTruce", "LIVE_QLOO" if args.live else "OFFLINE_FIXTURE", "at http://127.0.0.1:" + str(args.port))
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
