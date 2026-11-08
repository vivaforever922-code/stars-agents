import os, http.server, socketserver, urllib.parse, threading, time
from dotenv import set_key
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

PORT = 8765
STATE = {}

CSS = "body{font-family:sans-serif;max-width:500px;margin:40px auto;padding:20px} input{width:100%;padding:8px;margin:6px 0;box-sizing:border-box} button{padding:10px 20px;background:#4CAF50;color:#fff;border:none;cursor:pointer} .msg{padding:10px;margin:10px 0;border-radius:4px} .ok{background:#d4edda;color:#155724} .err{background:#f8d7da;color:#721c24}"

def page(msg="", api_id="", api_hash="", phone="", codeform=""):
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>stars-agent setup</title>"
            "<style>%s</style></head><body><h2>stars-agent - Configuration</h2>%s"
            "<form method='POST' action='/save'>"
            "<label>API_ID (my.telegram.org)</label><input name='api_id' value='%s' required>"
            "<label>API_HASH</label><input name='api_hash' value='%s' required>"
            "<label>Telephone (avec indicatif pays, ex: +213...)</label><input name='phone' value='%s' required>"
            "<button type='submit'>Enregistrer et envoyer le code</button></form>%s</body></html>"
            ) % (CSS, msg, api_id, api_hash, phone, codeform)

HTML_CODE = "<form method='POST' action='/verify'><label>Code recu par SMS</label><input name='code' required><button type='submit'>Verifier</button></form>"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond(page())
    def do_POST(self):
        import asyncio
        n = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(n).decode())
        if self.path == "/save":
            api_id = data.get("api_id", [""])[0].strip()
            api_hash = data.get("api_hash", [""])[0].strip()
            phone = data.get("phone", [""])[0].strip()
            STATE.update(api_id=api_id, api_hash=api_hash, phone=phone)
            if not os.path.exists(".env"):
                open(".env", "w").close()
            set_key(".env", "TG_API_ID", api_id)
            set_key(".env", "TG_API_HASH", api_hash)
            set_key(".env", "TG_PHONE", phone)
            set_key(".env", "DAILY_POST_CAP", "25")
            set_key(".env", "POST_INTERVAL_MIN", "420")
            set_key(".env", "REPORT_HOUR", "20")
            import asyncio
            loop = asyncio.new_event_loop()
            STATE["loop"] = loop
            def run_loop():
                asyncio.set_event_loop(loop)
                loop.run_forever()
            threading.Thread(target=run_loop, daemon=True).start()
            async def do_send():
                client = TelegramClient(StringSession(), int(api_id), api_hash, loop=loop)
                await client.connect()
                await client.send_code_request(phone)
                STATE["client"] = client
                STATE["sent"] = True
            try:
                fut = asyncio.run_coroutine_threadsafe(do_send(), loop)
                fut.result(timeout=30)
            except Exception as e:
                STATE["error"] = str(e)
            time.sleep(1)
            if STATE.get("error"):
                msg = '<div class="msg err">Erreur: %s</div>' % STATE["error"]
                self.respond(page(msg=msg, api_id=api_id, api_hash=api_hash, phone=phone))
            else:
                self.respond(page(msg='<div class="msg ok">Code envoye. Saisissez-le ci-dessous.</div>',
                    api_id=api_id, api_hash=api_hash, phone=phone, codeform=HTML_CODE))
        elif self.path == "/verify":
            code = data.get("code", [""])[0].strip()
            client = STATE.get("client")
            phone = STATE.get("phone")
            loop = STATE.get("loop")
            try:
                async def do_verify():
                    await client.sign_in(phone, code)
                    return client.session.save()
                session = asyncio.run_coroutine_threadsafe(do_verify(), loop).result(timeout=30)
                set_key(".env", "TG_SESSION", session)
                client.disconnect()
                self.respond(page(msg='<div class="msg ok">Configuration terminee ! Lancez python validate.py puis python main.py</div>',
                    api_id=STATE["api_id"], api_hash=STATE["api_hash"], phone=phone))
            except Exception as e:
                self.respond(page(msg='<div class="msg err">Erreur: %s</div>' % e,
                    api_id=STATE["api_id"], api_hash=STATE["api_hash"], phone=phone, codeform=HTML_CODE))
    def respond(self, body):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(body.encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    print("Ouvrez http://localhost:%d dans votre navigateur" % PORT)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()