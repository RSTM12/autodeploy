"""
ClawPump Auto Deploy Script
- Cek saldo gasless tiap 5 detik
- Rotate IP via Tor tiap deploy
- Kirim hasil ke Telegram
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
DELAY_ANTAR_LAUNCH  = 5   # jeda antar deploy (detik)
DELAY_CEK_TREASURY  = 5   # jeda cek ulang saldo (detik)
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

# ── Telegram ──────────────────────────────

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

# ── Tor ───────────────────────────────────

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
        print("  [!] Tor tidak aktif")
        return False
    try:
        lama = get_ip()
        with stem.control.Controller.from_port(port=9051) as c:
            c.authenticate()
            c.signal(stem.Signal.NEWNYM)
        print(f"  🔄 Rotate {lama} →", end=" ", flush=True)
        for _ in range(20):
            time.sleep(3)
            baru = get_ip()
            if baru and baru != lama:
                print(f"{baru} ✅")
                return True
        print(f"sama, lanjut")
        return True
    except Exception as e:
        print(f"  [!] Rotate error: {e}")
        return False

# ── Treasury ──────────────────────────────

def cek_saldo():
    try:
        r = requests.get(f"{CLAWPUMP_BASE}/api/treasury", timeout=15)
        d = r.json()
        affordable = d.get("wallet", {}).get("launchesAffordable", 0)
        status = d.get("status", "")
        return status == "healthy" and affordable > 0, affordable
    except:
        return False, 0

# ── Gambar ────────────────────────────────

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

# ── ClawPump API ──────────────────────────

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

# ── Simpan hasil ──────────────────────────

def simpan(baris):
    with open("results.txt", "a", encoding="utf-8") as f:
        f.write(baris + "\n")

# ── Load keys ─────────────────────────────

def load_keys():
    if not os.path.exists("keys.txt"):
        print("❌ File keys.txt tidak ada!")
        print("   Buat dulu: nano keys.txt")
        print("   Isi satu cpk_ key per baris")
        return []
    with open("keys.txt") as f:
        keys = [l.strip() for l in f if l.strip().startswith("cpk_")]
    return keys

# ── MAIN ──────────────────────────────────

def main():
    print("=" * 50)
    print("  🦞 ClawPump Auto Deploy v2 — Termux")
    print("=" * 50)

    if "isi_token" in BOT_TOKEN or "isi_chat" in CHAT_ID:
        print("\n⚠️  Edit dulu BOT_TOKEN dan CHAT_ID di atas!")
        return

    if not tor_aktif():
        print("\n❌ Tor tidak aktif! Jalankan: tor &")
        print("   Tunggu 'Bootstrapped 100%' lalu coba lagi")
        return

    ip = get_ip()
    print(f"\n✅ Tor aktif | IP: {ip}")

    keys = load_keys()
    if not keys:
        return

    print(f"📋 Total keys: {len(keys)}\n")

    tg(
        f"🚀 *Auto Deploy Dimulai*\n"
        f"📋 Keys: `{len(keys)}`\n"
        f"🔒 Tor IP: `{ip}`"
    )

    sukses = gagal = limit = 0

    for i, api_key in enumerate(keys, 1):
        ks = api_key[:18] + "..."
        print(f"[{i}/{len(keys)}] {ks}")

        # Cek saldo gasless
        print(f"  💰 Cek saldo...", end=" ", flush=True)
        coba = 0
        while True:
            ok, affordable = cek_saldo()
            if ok:
                print(f"✅ ({affordable} launches tersedia)")
                break
            coba += 1
            if coba == 1:
                print(f"kosong, tunggu...")
                tg(f"⏳ *Saldo Gasless Kosong*\nKey {i}: `{ks}`\nCek ulang tiap {DELAY_CEK_TREASURY}s...")
            time.sleep(DELAY_CEK_TREASURY)
            print(f"  💰 Cek ulang #{coba+1}...", end=" ", flush=True)

        # Rotate IP
        rotate_ip()

        # Generate token
        name   = random.choice(NAMES) + str(random.randint(10, 9999))
        symbol = random.choice(SYMBOLS)
        desc   = random.choice(DESCRIPTIONS)
        print(f"  📝 {name} (${symbol})")

        # Upload gambar
        print(f"  🖼️  Upload...", end=" ", flush=True)
        buf = buat_gambar(symbol)
        img_url = upload(buf)
        if not img_url:
            print("GAGAL ❌")
            gagal += 1
            simpan(f"[FAIL-UPLOAD] {api_key}")
            tg(f"❌ *Upload Gagal*\nKey: `{ks}`")
            continue
        print("OK ✅")

        # Launch
        print(f"  🚀 Launch...", end=" ", flush=True)
        hasil = launch(api_key, name, symbol, desc, img_url)

        if hasil.get("success"):
            pump_url = hasil.get("pumpUrl", "-")
            mint     = hasil.get("mintAddress", "-")
            explorer = hasil.get("explorerUrl", "-")
            print(f"SUKSES ✅")
            print(f"  🔗 {pump_url}")
            sukses += 1
            simpan(f"[OK] {api_key} | {name} | {symbol} | {mint} | {pump_url}")
            tg(
                f"✅ *Deploy Sukses!*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🪙 *Nama:* `{name}`\n"
                f"💲 *Symbol:* `${symbol}`\n"
                f"🔑 *Key:* `{ks}`\n"
                f"📍 *Mint:* `{mint}`\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 [Pump\.fun]({pump_url})\n"
                f"🔍 [Explorer]({explorer})"
            )

        elif hasil.get("_sc") == 429:
            jam = hasil.get("retryAfterHours", "?")
            print(f"RATE LIMITED ⏳ ({jam} jam)")
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

    # Summary
    print("\n" + "=" * 50)
    print(f"  ✅ Sukses: {sukses} | ⏳ Limit: {limit} | ❌ Gagal: {gagal}")
    print("=" * 50)
    tg(
        f"🏁 *Selesai!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Sukses: *{sukses}*\n"
        f"⏳ Rate limit: *{limit}*\n"
        f"❌ Gagal: *{gagal}*"
    )

if __name__ == "__main__":
    main()
