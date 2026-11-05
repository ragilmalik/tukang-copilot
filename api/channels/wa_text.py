"""Everything the WhatsApp channel says, in Bahasa Indonesia, Basa Jawa and English, plus the small language guess
that lets the chat follow the owner's own words (the web app has a language switch; a chat has only the text)."""
from __future__ import annotations

import re

T: dict[str, dict[str, str]] = {
    "welcome": {
        "id": "Halo! Saya Tukang Copilot. Kirim foto barang yang rusak (sampai 3) dan ceritakan masalahnya, boleh ketik atau pesan suara. "
              "Saya tandai bagiannya, cari penyebabnya, lalu pandu langkah demi langkah.",
        "jv": "Halo! Aku Tukang Copilot. Kirimen foto barang sing rusak (nganti 3) lan critakna masalahe, oleh ketik utawa pesen swara. "
              "Aku nandhani bageane, golek sebabe, banjur nuntun langkah siji-siji.",
        "en": "Hi! I'm Tukang Copilot. Send a photo of the broken thing (up to 3) and tell me what's wrong, typed or as a voice note. "
              "I mark the parts, find the likely cause, then guide you step by step.",
    },
    "ask_photo": {
        "id": "Siap. Sekarang kirim foto barang yang rusak ya (sampai 3 foto).",
        "jv": "Siap. Saiki kirimen foto barang sing rusak ya (nganti 3 foto).",
        "en": "Got it. Now send a photo of the broken thing (up to 3 photos).",
    },
    "ask_text": {
        "id": "Fotonya sudah masuk. Ceritakan masalahnya: ketik atau kirim pesan suara.",
        "jv": "Fotone wis mlebu. Critakna masalahe: ketik utawa kirim pesen swara.",
        "en": "Got the photo. Tell me what's wrong: type it or send a voice note.",
    },
    "working": {
        "id": "Sebentar, saya periksa fotonya (sekitar 1 menit)...",
        "jv": "Sedhela, takpriksa fotone (kira-kira 1 menit)...",
        "en": "One moment, checking your photo (about a minute)...",
    },
    "unsupported": {
        "id": "Saya bisa membaca teks, foto, dan pesan suara. Coba kirim salah satunya.",
        "jv": "Aku bisa maca teks, foto, lan pesen swara. Jajal kirim salah sijine.",
        "en": "I can read text, photos and voice notes. Please send one of those.",
    },
    "too_long": {
        "id": "Pesannya terlalu panjang (maksimal 2000 huruf). Coba lebih singkat.",
        "jv": "Pesene kedawan (paling akeh 2000 aksara). Jajal luwih cekak.",
        "en": "That message is too long (2000 characters max). Please keep it shorter.",
    },
    "too_big": {
        "id": "Filenya terlalu besar. Kirim foto di bawah 15 MB atau pesan suara di bawah 20 MB.",
        "jv": "Filene kegedhen. Kirim foto ing ngisor 15 MB utawa pesen swara ing ngisor 20 MB.",
        "en": "That file is too big. Send photos under 15 MB and voice notes under 20 MB.",
    },
    "bad_photo": {
        "id": "Fotonya tidak bisa dibaca. Coba foto lagi (JPG atau PNG).",
        "jv": "Fotone ora bisa diwaca. Jajal motret maneh (JPG utawa PNG).",
        "en": "I couldn't read that photo. Please take it again (JPG or PNG).",
    },
    "bad_audio": {
        "id": "Pesan suaranya tidak bisa dibaca. Coba rekam lagi, atau ketik saja.",
        "jv": "Pesen swarane ora bisa diwaca. Jajal ngrekam maneh, utawa ketik wae.",
        "en": "I couldn't read that voice note. Please record it again, or type it.",
    },
    "media_failed": {
        "id": "Filenya gagal diunduh dari WhatsApp. Coba kirim lagi.",
        "jv": "Filene gagal diundhuh saka WhatsApp. Jajal kirim maneh.",
        "en": "I couldn't download that file from WhatsApp. Please send it again.",
    },
    "step": {"id": "Langkah {n} dari {total}", "jv": "Langkah {n} saka {total}", "en": "Step {n} of {total}"},
    "before": {"id": "Sebelum mulai:", "jv": "Sadurunge miwiti:", "en": "Before you start:"},
    "send_check": {
        "id": "📷 Kirim foto setelah selesai, saya cek.",
        "jv": "📷 Kirim foto yen wis rampung, takcek.",
        "en": "📷 Send a photo when it's done and I'll check it.",
    },
    "wait": {"id": "⏱ Tunggu {m} menit.", "jv": "⏱ Enteni {m} menit.", "en": "⏱ Wait {m} min."},
    "btn_done": {"id": "Selesai", "jv": "Rampung", "en": "Done"},
    "btn_problem": {"id": "Ada masalah", "jv": "Ana masalah", "en": "Problem"},
    "btn_stop": {"id": "Berhenti", "jv": "Mandheg", "en": "Stop"},
    "btn_retry": {"id": "Coba lagi", "jv": "Jajal maneh", "en": "Try again"},
    # simulator "after photo" button: the labelled sample photo shows one step, so it is checked on that step
    # (api/sample_step.py), the same lines as the web app's sampleFor / sampleForLast
    "sample_for": {
        "id": "Foto contoh ini dicek untuk langkah {n}, langkah yang ditunjukkan fotonya.",
        "jv": "Foto conto iki dipriksa kanggo langkah {n}, langkah sing dituduhake fotone.",
        "en": "Checking step {n} with this sample photo: it is the step the photo shows.",
    },
    "sample_for_last": {
        "id": "Foto contoh ini dicek untuk langkah terakhir ({n}).",
        "jv": "Foto conto iki dipriksa kanggo langkah pungkasan ({n}).",
        "en": "Checking the last step ({n}) with this sample photo.",
    },
    "check_fail_hint": {
        "id": "Coba foto lagi, atau ketuk Ada masalah.",
        "jv": "Jajal motret maneh, utawa tutul Ana masalah.",
        "en": "Try another photo, or tap Problem.",
    },
    "replan": {"id": "🔁 Rencana {k}: {cause}", "jv": "🔁 Rencana {k}: {cause}", "en": "🔁 Plan {k}: {cause}"},
    "done": {"id": "🎉 Semua langkah selesai!", "jv": "🎉 Kabeh langkah rampung!", "en": "🎉 All steps done!"},
    "final_check": {"id": "Cek akhir:", "jv": "Cek pungkasan:", "en": "Final check:"},
    "report_caption": {
        "id": "Laporan perbaikan (PDF), bisa ditunjukkan ke bengkel.",
        "jv": "Laporan ndandani (PDF), bisa dituduhake menyang bengkel.",
        "en": "Repair report (PDF), ready to show a workshop.",
    },
    "stopped": {"id": "Panduan dihentikan.", "jv": "Pandhuan dimandhegake.", "en": "Guide stopped."},
    "stop_title": {"id": "⛔ Dihentikan demi keselamatan", "jv": "⛔ Dimandhegake kanggo keslametan", "en": "⛔ Stopped for your safety"},
    "workshop": {"id": "📍 Bengkel/servis terdekat: {url}", "jv": "📍 Bengkel/servis paling cedhak: {url}", "en": "📍 Nearest workshop: {url}"},
    "emergency": {"id": "Darurat: 112", "jv": "Darurat: 112", "en": "Emergency: 112"},
    "erase_hint": {
        "id": "Ketik HAPUS untuk menghapus foto dan data perbaikan ini sekarang.",
        "jv": "Ketik BUSAK kanggo mbusak foto lan data ndandani iki saiki.",
        "en": "Type DELETE to erase your photos and this repair now.",
    },
    "erased": {
        "id": "Foto dan data perbaikanmu sudah dihapus dari server.",
        "jv": "Foto lan data ndandanimu wis dibusak saka server.",
        "en": "Your photos and repair data are erased from the server.",
    },
    "new_hint": {
        "id": "Kirim foto baru kapan saja untuk perbaikan berikutnya.",
        "jv": "Kirim foto anyar kapan wae kanggo ndandani sabanjure.",
        "en": "Send a new photo any time for the next repair.",
    },
    "reset": {
        "id": "Oke, mulai dari awal. Kirim foto barang yang rusak.",
        "jv": "Oke, miwiti saka wiwitan. Kirimen foto barang sing rusak.",
        "en": "OK, starting over. Send a photo of the broken thing.",
    },
    "stale": {
        "id": "Tombol itu dari pesan lama. Ini langkah sekarang:",
        "jv": "Tombol kuwi saka pesen lawas. Iki langkah saiki:",
        "en": "That button is from an older message. Here is the current step:",
    },
    "not_understood": {
        "id": "Ketuk tombol di bawah, kirim foto untuk dicek, atau ketik \"masih rusak\".",
        "jv": "Tutul tombol ing ngisor, kirim foto kanggo dicek, utawa ketik \"isih rusak\".",
        "en": "Tap a button below, send a photo to check, or type \"still broken\".",
    },
    "voice_unknown": {
        "id": "Maaf, perintahnya tidak tertangkap. Ketuk tombol di bawah.",
        "jv": "Ngapura, dhawuhe ora krungu. Tutul tombol ing ngisor.",
        "en": "Sorry, I didn't catch that. Tap a button below.",
    },
    "ask_photo_check": {
        "id": "Kirim fotonya, saya cek langkah ini.",
        "jv": "Kirimen fotone, takcek langkah iki.",
        "en": "Send the photo and I'll check this step.",
    },
    "answer_first": {
        "id": "Jawab pertanyaan ini dulu ya (ketik atau pesan suara):",
        "jv": "Wangsuli pitakon iki dhisik ya (ketik utawa pesen swara):",
        "en": "Please answer this first (typed or voice note):",
    },
    "limit": {
        "id": "Cek foto untuk perbaikan ini sudah habis. Ketuk Ada masalah atau Berhenti.",
        "jv": "Cek foto kanggo ndandani iki wis entek. Tutul Ana masalah utawa Mandheg.",
        "en": "This repair has used all its photo checks. Tap Problem or Stop.",
    },
    "demo": {"id": "🧪 Mode contoh offline (jawaban contoh tertulis)", "jv": "🧪 Mode conto offline (jawaban conto)",
             "en": "🧪 Offline sample mode (pre-written answers)"},
    "fallback": {"id": "Sebagian jawaban contoh (AI live tidak tersedia)", "jv": "Sapérangan jawaban conto (AI live ora ana)",
                 "en": "Some sample answers (live AI unavailable)"},
    "safety": {"id": "Keamanan", "jv": "Keslametan", "en": "Safety"},
    "level_green": {"id": "hijau, aman dikerjakan sendiri", "jv": "ijo, aman digarap dhewe", "en": "green, safe to do yourself"},
    "level_amber": {"id": "kuning, hati-hati", "jv": "kuning, ati-ati", "en": "amber, take care"},
    "level_red": {"id": "merah", "jv": "abang", "en": "red"},
    "cost_parts": {"id": "💰 Suku cadang ~{parts}", "jv": "💰 Onderdil ~{parts}", "en": "💰 Parts ~{parts}"},
    "cost_save": {"id": " · bengkel ~{shop} · hemat ~{save}", "jv": " · bengkel ~{shop} · irit ~{save}",
                  "en": " · workshop ~{shop} · you save ~{save}"},
    "minutes": {"id": "⏱ ~{m} menit", "jv": "⏱ ~{m} menit", "en": "⏱ ~{m} min"},
    "footer": {"id": "Tukang Copilot", "jv": "Tukang Copilot", "en": "Tukang Copilot"},
    "footer_demo": {"id": "Tukang Copilot · contoh offline", "jv": "Tukang Copilot · conto offline", "en": "Tukang Copilot · offline sample"},
}


def t(key: str, lang: str, **kw: object) -> str:
    row = T[key]
    s = row.get(lang) or row["id"]
    return s.format(**kw) if kw else s


# Words that mostly belong to one of the three languages. Shared words (rusak, mati, motor) are left out on purpose.
_MARKERS: dict[str, set[str]] = {
    "jv": {"aku", "ora", "wis", "durung", "piye", "kepiye", "opo", "karo", "sing", "iki", "kuwi", "mung", "nanging", "lan",
           "urip", "muni", "banyune", "kudu", "arep", "ana", "isih", "wae", "ae", "ngapa", "kok", "nggih", "mboten", "sampun",
           "dereng", "kulo", "kula", "panjenengan", "sampeyan", "kowe", "rampung", "mbok", "saiki", "wingi", "esuk", "mambu",
           "gase", "motorku", "omahku", "pawon", "tulung", "jajal", "ngene", "ngono", "senajan", "babar", "pisan", "lho", "yo",
           "dadi", "metu", "mlebu", "angel", "apik", "elek", "anyar", "lawas", "banyu", "dhewe", "ngisor", "nduwur", "neng", "ning"},
    "id": {"saya", "tidak", "nggak", "gak", "enggak", "yang", "dan", "sudah", "bisa", "mau", "tolong", "ini", "itu", "tapi",
           "padahal", "kenapa", "bagaimana", "gimana", "masih", "belum", "keluar", "hidup", "nyala", "bunyi", "airnya", "sekali",
           "banget", "aku", "kok", "dari", "dengan", "untuk", "pada", "ada", "tetap", "terus", "walaupun", "sama", "lagi", "kalau",
           "pagi", "susah", "mesin", "dapur", "rumah", "bocor", "kami", "kita", "jadi", "baru", "lama", "air", "tadi", "buat"},
    "en": {"the", "my", "is", "it", "won't", "doesn't", "don't", "not", "and", "with", "please", "when", "even", "though",
           "keeps", "dripping", "broken", "start", "starts", "water", "comes", "out", "there", "what", "how", "why", "this",
           "that", "i", "it's", "won", "help", "fix", "leak", "leaking", "smell", "turn", "on", "off", "of", "a", "an", "to",
           "but", "since", "morning", "engine", "tap", "tyre", "tire", "flat", "pump", "still", "just", "plugged", "light"},
}


def detect(text: str) -> str | None:
    """id, jv or en when the words lean clearly one way; None when unsure (the chat keeps its current language).
    Javanese shares many words with Indonesian, so only words that are Javanese-only count for jv."""
    words = re.findall(r"[a-z']+", (text or "").lower())
    jv_only = sum(1 for w in words if w in _MARKERS["jv"] and w not in _MARKERS["id"])
    id_only = sum(1 for w in words if w in _MARKERS["id"] and w not in _MARKERS["jv"])
    en = sum(1 for w in words if w in _MARKERS["en"])
    if jv_only and jv_only >= id_only and jv_only >= en:
        return "jv"
    idn = sum(1 for w in words if w in _MARKERS["id"])
    if idn > en:
        return "id"
    if en > idn:
        return "en"
    return None


ERASE = {"hapus", "busak", "delete", "erase", "hapus data", "busak data"}
RESET = {"baru", "anyar", "new", "reset", "mulai lagi", "mulai baru", "start over"}
HELLO = {"halo", "hallo", "hai", "hi", "hello", "help", "bantuan", "menu", "start", "mulai", "sugeng", "assalamualaikum", "p"}


def command(text: str) -> str | None:
    """Whole-message chat commands: erase, reset, hello."""
    t_ = " ".join(re.sub(r"[^\w ]+", " ", (text or "").lower()).split())
    if t_ in ERASE:
        return "erase"
    if t_ in RESET:
        return "reset"
    if t_ in HELLO:
        return "hello"
    return None


def rupiah(n: int | float | None) -> str:
    return "Rp " + f"{int(n or 0):,}".replace(",", ".")
