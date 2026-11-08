import asyncio, sys
from telethon.tl import functions
import tg

async def main():
    c = await tg.get_client()
    ok, ko = [], []
    for line in open("targets.txt"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            ent = await c.get_entity(line)
            full = await c(functions.channels.GetFullChannelRequest(ent))
            if full.full_chat.participants_count < 50:
                ko.append((line, "moins de 50 membres"))
                continue
            ok.append((line, full.full_chat.participants_count))
            print(f"OK   {line} ({full.full_chat.participants_count} membres)")
        except Exception as e:
            ko.append((line, type(e).__name__))
            print(f"KO   {line} ({type(e).__name__})")
    with open("targets_valid.txt", "w") as f:
        f.write("# généré par validate.py\n")
        for l, _ in ok:
            f.write(l + "\n")
    print(f"\n{len(ok)} valides, {len(ko)} rejetées")

asyncio.run(main())
