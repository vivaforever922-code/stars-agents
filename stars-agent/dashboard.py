import http.server, socketserver, sqlite3, os, datetime, urllib.parse, asyncio, threading

PORT = 8780
DB = "agent.db"
CHAT = {"busy": False}
HISTORY = []

def q(sql, params=()):
    if not os.path.exists(DB):
        return []
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def exec_sql(sql, params=()):
    con = sqlite3.connect(DB)
    con.execute(sql, params)
    con.commit()
    con.close()

def tail_log(n=80):
    if not os.path.exists("agent.log"):
        return "(aucun log pour l'instant - lancez python main.py)"
    with open("agent.log", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-n:])

def llm_chat(msg):
    try:
        import llm
        return asyncio.run(llm.complete("Tu es l'agent stars-agent. Reponds de facon concise et utile: " + msg))
    except Exception as e:
        return "Erreur LLM: " + str(e)

def run_chat(msg):
    CHAT["busy"] = True
    reply = llm_chat(msg)
    HISTORY.append((msg, reply))
    CHAT["busy"] = False

def html_page():
    programs = q("SELECT * FROM programs ORDER BY created_at DESC LIMIT 50")
    posts = q("SELECT * FROM posts ORDER BY sent_at DESC LIMIT 50")
    balances = q("SELECT * FROM balances ORDER BY ts DESC LIMIT 20")
    missions = q("SELECT * FROM missions ORDER BY created_at DESC LIMIT 50")
    joined = sum(1 for p in programs if p.get("joined"))
    mission_rows = "".join("<tr><td><a href=\"/logs\">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (m.get("id"), m.get("text"), m.get("status"), m.get("created_at")) for m in missions)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    css = "body{font-family:sans-serif;margin:20px;background:#111;color:#eee} h1,h2{color:#4CAF50} table{border-collapse:collapse;width:100%;margin:10px 0} th,td{border:1px solid #333;padding:6px;text-align:left;font-size:13px} th{background:#222} .card{background:#1a1a1a;padding:15px;margin:10px 0;border-radius:8px;display:inline-block;min-width:180px} .stat{font-size:28px;font-weight:bold;color:#4CAF50} input,textarea{width:100%;padding:8px;margin:6px 0;box-sizing:border-box;background:#222;color:#eee;border:1px solid #444} button{padding:10px 20px;background:#4CAF50;color:#fff;border:none;cursor:pointer} pre{background:#000;padding:10px;border-radius:6px;overflow:auto;max-height:400px;font-size:12px} .chatbox{background:#1a1a1a;padding:15px;margin:10px 0;border-radius:8px} .msg-user{color:#4CAF50;margin:8px 0} .msg-agent{color:#eee;margin:8px 0 16px 0;white-space:pre-wrap} .thinking{color:#888;font-style:italic}"
    # build conversation html
    convo = ""
    for u, a in HISTORY:
        convo += "<div class='msg-user'><b>Vous:</b> " + u.replace("<","&lt;").replace(">","&gt;") + "</div>"
        convo += "<div class='msg-agent'><b>Agent:</b> " + a.replace("<","&lt;").replace(">","&gt;") + "</div>"
    if CHAT["busy"]:
        convo += "<div class='thinking'>L'agent reflechit...</div>"
    chatbox = ("<h2>Chat avec l'agent IA</h2><div class='chatbox'>" + convo +
               "<form method='POST' action='/'><textarea name='msg' rows='2' placeholder='Donnez un ordre a l agent...'></textarea><br><button type='submit'>Envoyer</button></form></div>")
    return ("<html><head><meta charset='utf-8'><title>stars-agent dashboard</title><style>" + css + "</style></head><body>"
            "<h1>stars-agent Dashboard</h1><p><a href='/logs'>Logs</a></p>"
            + chatbox +
            "<h2>Missions</h2><table><tr><th>ID</th><th>Texte</th><th>Status</th><th>Cree</th></tr>" + mission_rows + "</table>"
            "</body></html>")

def logs_page():
    css = "body{font-family:monospace;margin:20px;background:#000;color:#0f0} pre{white-space:pre-wrap;font-size:12px} a{color:#4CAF50}"
    return ("<html><head><meta charset='utf-8'><title>logs</title><style>" + css + "</style></head><body>"
            "<h2>Logs temps reel - <a href='/'>Dashboard</a></h2>"
            "<pre>" + tail_log(120).replace("<", "&lt;").replace(">", "&gt;") + "</pre></body></html>")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/logs":
            body = logs_page().encode()
        else:
            body = html_page().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(n).decode())
        if self.path == "/mission":
            text = data.get("text", [""])[0].strip()
            if text:
                exec_sql("INSERT INTO missions(text, status, created_at) VALUES (?,?,?)",
                         (text, "pending", datetime.datetime.now().isoformat()))
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        elif self.path == "/":
            msg = data.get("msg", [""])[0].strip()
            if msg and not CHAT["busy"]:
                threading.Thread(target=run_chat, args=(msg,), daemon=True).start()
            body = html_page().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass

if __name__ == "__main__":
    print("Dashboard: http://localhost:%d" % PORT)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()