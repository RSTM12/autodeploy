"""
ClawPump Auto Deploy Script - SPEED MODE
- Siapkan semua (IP, gambar, token) SAMBIL nunggu saldo
- Cek saldo tiap 1 detik
- Begitu saldo ada langsung launch dalam hitungan detik!
"""

import requests
import random
import time
import socket
import os
import stem
import stem.control
from PIL import Image, ImageDraw
from io import BytesIO

# ══════════════════════════════════════════
#   CONFIG — EDIT BAGIAN INI
# ══════════════════════════════════════════
BOT_TOKEN = "isi_token_bot_telegram_kamu"
CHAT_ID   = "isi_chat_id_kamu"

CLAWPUMP_BASE       = "https://clawpump.tech"
DELAY_ANTAR_LAUNCH  = 3
DELAY_CEK_TREASURY  = 1
# ══════════════════════════════════════════

TOR_SOCKS = {
    "http":  "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

NAMES = [
    "SolFlare","MoonDog","PumpKing","DegenApe","RocketCat",
    "StarFrog","CryptoFox","NeonBear","PixelWolf","LaserEagle",
    "CosmicRat","TurboShib","MegaPepe","UltraBull","SonicDoge",
    "GalaxyCat","PlutoFi","NovaDegen","HyperPump","ZenithCoin",
    "BlazeDog","QuantumCat","NebulaPepe","VortexApe","LunarFox",
]

SYMBOLS = [
    "SFL","MDOG","PKING","DAPE","RCAT",
    "SFRG","CFOX","NBEAR","PWOLF","LEAGL",
    "CRAT","TSHIB","MPEPE","UBULL","SDOGE",
    "GCAT","PLUTO","NDGN","HPUMP","ZNTH",
    "BLZD","QCAT","NBPP","VAPE","LFOX",
]

DESCRIPTIONS = [
    "The most degenerate token on Solana. Built by degens, for degens.",
    "To the moon and beyond! Join the rocket ship before it is too late.",
    "Community-driven token with zero utility but maximum vibes only.",
    "The future of finance is here. Ape in before it pumps to the top.",
    "Born on pump.fun, destined for greatness. LFG to the moon now!",
    "Just a cat riding a rocket to the moon. Nothing else matters now.",
    "Diamond hands only. Paper hands will be left behind forever here.",
    "The most based token in the Solana ecosystem. Period. No cap ever.",
    "We are all gonna make it. Buy now, regret never. WAGMI forever.",
    "100x potential minimum. Degen responsibly and enjoy the ride up.",
]

COLORS = [
    (255, 80, 80),  (80, 200, 80),  (80, 80, 255),
    (255, 180, 30), (180, 30, 255), (30, 220, 180),
    (255, 120, 30), (30, 120, 255), (255, 30, 120),
    (100, 200, 255),(255, 200, 100),(200, 100, 255),
]

def tg(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"  [TG ERROR] {e}")

def tor_aktif():
    try:
        s = socket.create_connection(("127.0.0.1", 9050), timeout=2)
        s.close()
        return True
    except:
        return False

def get_ip():
    try:
        r = requests.get(
            "https://api.ipify.org?format=json",
            proxies=TOR_SOCKS, timeout=10
        )
        return r.json().get("ip", "?")
    except:
        return "?"

def rotate_ip():
    if not tor_aktif():
        return False
    try:
        lama = get_ip()
        with stem.control.Controller.from_port(port=9051) as c:
            c.authenticate()
            c.signal(stem.Signal.NEWNYM)
        for _ in range(20):
            time.sleep(3)
            baru = get_ip()
            if baru and baru != lama:
                return True
        return True
    except:
        return False

def cek_saldo():
    try:
        r = requests.get(
            f"{CLAWPUMP_BASE}/api/treasury",
            timeout=5
        )
        d = r.json()
        affordable = d.get("wallet", {}).get("launchesAffordable", 0)
        status = d.get("status", "")
        return status == "healthy" and affordable > 0, affordable
    except:
        return False, 0

def buat_gambar(symbol):
    size = 512
    warna = random.choice(COLORS)
    img = Image.new("RGB", (size, size), color=warna)
    draw = ImageDraw.Draw(img)
    gelap = tuple(max(0, c - 60) for c in warna)
    draw.ellipse([40, 40, size-40, size-40], fill=gelap)
    draw.text((size//2 - 60, size//2 - 20), symbol[:5], fill="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def upload(buf):
    try:
        r = requests.post(
            f"{CLAWPUMP_BASE}/api/upload",
            files={"image": ("token.png", buf, "image/png")},
            proxies=TOR_SOCKS, timeout=30,
        )
        d = r.json()
        return d.get("imageUrl") if d.get("success") else None
    except Exception as e:
        print(f"  [!] Upload error: {e}")
        return None

def launch(api_key, name, symbol, desc, image_url):
    try:
        r = requests.post(
            f"{CLAWPUMP_BASE}/api/launch",
            json={
                "name": name,
                "symbol": symbol,
                "description": desc,
                "imageUrl": image_url,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            proxies=TOR_SOCKS, timeout=60,
        )
        d = r.json()
        d["_sc"] = r.status_code
        return d
    except Exception as e:
        return {"success": False, "error": str(e), "_sc": 0}

def simpan(baris):
    with open("results.txt", "a", encoding="utf-8") as f:
        f.write(baris + "\n")

def load_keys():
    if not os.path.exists("keys.txt"):
        print("❌ File keys.txt tidak ada!")
        return []
    with open("keys.txt") as f:
        keys = [l.strip() for l in f if l.strip().startswith("cpk_")]
    return keys

def persiapan(nomor, total):
    print(f"\n  ⚙️  Persiapan [{nomor}/{total}]...")

    name   = random.choice(NAMES) + str(random.randint(10, 9999))
    symbol = random.choice(SYMBOLS)
    desc   = random.choice(DESCRIPTIONS)
    print(f"  📝 Token: {name} (${symbol})")

    print(f"  🔄 Rotate IP...", end=" ", flush=True)
    rotate_ip()
    ip_baru = get_ip()
    print(f"{ip_baru} ✅")

    print(f"  🖼️  Upload gambar...", end=" ", flush=True)
    buf = buat_gambar(symbol)
    img_url = upload(buf)
    if img_url:
        print(f"OK ✅")
    else:
        print(f"GAGAL ❌")

    return {
        "name": name,
        "symbol": symbol,
        "desc": desc,
        "img_url": img_url,
        "ip": ip_baru,
    }

def main():
    print("=" * 50)
    print("  🦞 ClawPump Auto Deploy — SPEED MODE ⚡")
    print("=" * 50)

    if "isi_token" in BOT_TOKEN or "isi_chat" in CHAT_ID:
        print("\n⚠️  Edit dulu BOT_TOKEN dan CHAT_ID di atas!")
        return

    if not tor_aktif():
        print("\n❌ Tor tidak aktif! Jalankan: tor &")
        return

    ip = get_ip()
    print(f"\n✅ Tor aktif | IP: {ip}")

    keys = load_keys()
    if not keys:
        return

    print(f"📋 Total keys: {len(keys)}")
    print(f"⚡ Mode: SPEED (cek saldo tiap {DELAY_CEK_TREASURY} detik)\n")

    tg(
        f"🚀 *Auto Deploy SPEED MODE*\n"
        f"📋 Keys: `{len(keys)}`\n"
        f"⚡ Cek saldo tiap `{DELAY_CEK_TREASURY}` detik\n"
        f"🔒 Tor IP: `{ip}`"
    )

    sukses = gagal = limit = 0

    for i, api_key in enumerate(keys, 1):
        ks = api_key[:18] + "..."
        print(f"\n{'='*50}")
        print(f"[{i}/{len(keys)}] Key: {ks}")

        prep = persiapan(i, len(keys))

        if not prep["img_url"]:
            gagal += 1
            simpan(f"[FAIL-UPLOAD] {api_key}")
            tg(f"❌ *Upload Gagal*\nKey: `{ks}`")
            continue

        print(f"\n  ⏳ Nunggu saldo gasless...", end=" ", flush=True)
        coba = 0
        while True:
            ok, affordable = cek_saldo()
            if ok:
                print(f"ADA! ({affordable} launches) ⚡")
                break
            coba += 1
            if coba % 10 == 0:
                print(f"\n  ⏳ Masih nunggu ({coba} detik)...", end=" ", flush=True)
            time.sleep(DELAY_CEK_TREASURY)

        print(f"  🚀 LAUNCH!", end=" ", flush=True)
        t_mulai = time.time()
        hasil = launch(api_key, prep["name"], prep["symbol"],
                       prep["desc"], prep["img_url"])
        t_selesai = time.time()
        durasi = round(t_selesai - t_mulai, 2)

        if hasil.get("success"):
            pump_url = hasil.get("pumpUrl", "-")
            mint     = hasil.get("mintAddress", "-")
            explorer = hasil.get("explorerUrl", "-")
            print(f"SUKSES dalam {durasi}s ✅")
            print(f"  🔗 {pump_url}")
            sukses += 1
            simpan(f"[OK] {api_key} | {prep['name']} | {prep['symbol']} | {mint} | {pump_url}")
            tg(
                f"✅ *Deploy Sukses!* ({durasi}s)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🪙 *Nama:* `{prep['name']}`\n"
                f"💲 *Symbol:* `${prep['symbol']}`\n"
                f"🔑 *Key:* `{ks}`\n"
                f"📍 *Mint:* `{mint}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 [Pump.fun]({pump_url})\n"
                f"🔍 [Explorer]({explorer})"
            )

        elif hasil.get("_sc") == 429:
            jam = hasil.get("retryAfterHours", "?")
            print(f"RATE LIMITED ⏳")
            limit += 1
            simpan(f"[LIMIT] {api_key} | {jam}h")
            tg(
                f"⏳ *Rate Limited*\n"
                f"🔑 Key: `{ks}`\n"
                f"⏰ Coba lagi: *{jam} jam*"
            )

        else:
            err = hasil.get("error") or hasil.get("message") or "unknown"
            print(f"GAGAL ❌ ({err})")
            gagal += 1
            simpan(f"[FAIL] {api_key} | {err}")
            tg(
                f"❌ *Deploy Gagal*\n"
                f"🔑 Key: `{ks}`\n"
                f"⚠️ `{err}`"
            )

        if i < len(keys):
            time.sleep(DELAY_ANTAR_LAUNCH)

    print(f"\n{'='*50}")
    print(f"  ✅ Sukses: {sukses} | ⏳ Limit: {limit} | ❌ Gagal: {gagal}")
    print(f"{'='*50}")
    tg(
        f"🏁 *Selesai!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Sukses: *{sukses}*\n"
        f"⏳ Rate limit: *{limit}*\n"
        f"❌ Gagal: *{gagal}*"
    )

if __name__ == "__main__":
    main()
