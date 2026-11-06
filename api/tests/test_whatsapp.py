"""WhatsApp channel against the fake Graph API (api/tests/doubles/fake_graph.py): the real webhook route, real httpx
calls, real multipart uploads and two-step media downloads, and the real engine in demo mode."""
import io
import logging
import shutil
import subprocess

import pytest
from PIL import Image

from api.channels import wa_sim, wa_text
from api.channels import whatsapp as wa
from api.main import app
from api.pipeline import engine
from api.tests.doubles import fake_graph as fg
from api.tests.owner_auth import OwnerClient

client = OwnerClient(app)
PHONE = "6281234567890"
SECRET = "test-app-secret"
VERIFY = "verify-me-123"
FAUCET_ID = "Kran wastafel dapur netes terus walaupun sudah ditutup kencang."
FAUCET_EN = "My kitchen tap keeps dripping even when it is closed tight."
RICE_ID = "Rice cooker saya nggak panas, lampunya mati padahal sudah dicolok."
GAS_JV = "Kompor gase bocor, aku kudu piye?"


@pytest.fixture(scope="module")
def graph_url():
    return fg.serve_in_thread()


@pytest.fixture(autouse=True)
def _wa(monkeypatch, graph_url):
    from api.settings import settings

    monkeypatch.setattr(settings, "wa_token", fg.TOKEN)
    monkeypatch.setattr(settings, "wa_phone_number_id", fg.PHONE_ID)
    monkeypatch.setattr(settings, "wa_verify_token", VERIFY)
    monkeypatch.setattr(settings, "wa_app_secret", SECRET)
    monkeypatch.setattr(settings, "wa_graph_base", graph_url)
    monkeypatch.setattr(settings, "wa_graph_version", "v26.0")
    monkeypatch.setattr(settings, "wa_debounce_s", 0.0)
    wa.reset()
    wa_sim.reset()
    fg.reset()
    yield
    assert wa.wait_idle(30)


def _jpg(color=(200, 200, 200), src=None):
    if src is not None:
        return src.read_bytes()
    b = io.BytesIO()
    Image.new("RGB", (640, 480), color).save(b, "JPEG")
    return b.getvalue()


def deliver(*messages, secret=SECRET, phone_number_id=fg.PHONE_ID):
    body = fg.encode(fg.webhook(list(messages), phone_number_id))
    r = client.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": fg.sign(body, secret),
                                                                  "Content-Type": "application/json"})
    assert wa.wait_idle(30)
    return r


def _sid() -> str:
    sid = wa._convs[wa.user_key(PHONE)].sid
    assert sid
    return sid


def sent_since(n):
    return fg.sent[n:]


def last_interactive():
    return [m for m in fg.sent if m["type"] == "interactive"][-1]["interactive"]


def button_ids(inter):
    return [b["reply"]["id"] for b in inter["action"]["buttons"]]


def photo(samples, name="faucet"):
    return fg.add_media(_jpg(src=samples[name]), "image/jpeg")


def tap(prefix):
    bid = next(b for b in button_ids(last_interactive()) if b.startswith(prefix + ":"))
    return deliver(fg.button_msg(PHONE, bid, prefix))


# --- webhook basics
def test_verify_handshake():
    r = client.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "1158201444"})
    assert r.status_code == 200 and r.text == "1158201444"
    bad = client.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "1"})
    assert bad.status_code == 403


def test_disabled_channel_is_404(monkeypatch):
    from api.settings import settings

    monkeypatch.setattr(settings, "wa_app_secret", "")
    assert client.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "1"}).status_code == 404
    body = fg.encode(fg.webhook([fg.text_msg(PHONE, "halo")]))
    assert client.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": fg.sign(body, "")}).status_code == 404


def test_bad_or_missing_signature_is_403_and_nothing_is_sent():
    body = fg.encode(fg.webhook([fg.text_msg(PHONE, "halo")]))
    assert client.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": fg.sign(body, "wrong")}).status_code == 403
    assert client.post("/webhooks/whatsapp", content=body).status_code == 403
    tampered = body.replace(b"halo", b"hola")
    assert client.post("/webhooks/whatsapp", content=tampered, headers={"X-Hub-Signature-256": fg.sign(body, SECRET)}).status_code == 403
    wa.wait_idle(5)
    assert fg.sent == []


def test_status_updates_and_other_business_numbers_are_ignored():
    body = fg.encode(fg.status_update(PHONE))
    r = client.post("/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": fg.sign(body, SECRET)})
    assert r.status_code == 200 and r.json()["queued"] == 0
    assert deliver(fg.text_msg(PHONE, "halo"), phone_number_id="999").json()["queued"] == 0
    assert fg.sent == []


def test_duplicate_delivery_is_handled_once():
    m = fg.text_msg(PHONE, "Kran saya netes terus", wamid="wamid.SAME1")
    assert deliver(m).json()["queued"] == 1
    assert deliver(m).json()["queued"] == 0  # Meta retried the same delivery
    assert len(fg.sent) == 1


# --- the chat
def test_text_only_asks_for_a_photo_and_starts_nothing(tmp_path):
    deliver(fg.text_msg(PHONE, "Motor saya susah hidup dari pagi"))
    assert len(fg.sent) == 1
    m = fg.sent[0]
    assert m["to"] == PHONE and m["messaging_product"] == "whatsapp" and m["type"] == "text"
    assert m["text"]["body"] == wa_text.t("ask_photo", "id")
    assert not (tmp_path / "sessions").exists()


def test_hello_gets_the_welcome():
    deliver(fg.text_msg(PHONE, "Halo"))
    assert "Tukang Copilot" in fg.sent[0]["text"]["body"]


def test_photo_flow_marked_photo_diagnosis_steps_and_pdf(samples):
    deliver(fg.text_msg(PHONE, FAUCET_ID))
    deliver(fg.image_msg(PHONE, photo(samples)))
    kinds = [m["type"] for m in fg.sent]
    assert kinds == ["text", "text", "image", "interactive"], kinds
    img = fg.sent[2]["image"]
    up = fg.uploads[img["id"]]
    assert up["mime"] == "image/jpeg" and up["data"][:2] == b"\xff\xd8"  # the SAM-marked parts.jpg
    cap = img["caption"]
    assert "🩺" in cap and "Rp" in cap and "hemat" in cap and "Mode contoh offline" in cap
    inter = fg.sent[3]["interactive"]
    assert inter["type"] == "button" and "Langkah 1 dari 4" in inter["body"]["text"]
    assert [b["reply"]["title"] for b in inter["action"]["buttons"]] == ["Selesai", "Ada masalah", "Berhenti"]
    assert all(b.startswith(("done:", "problem:", "stop:")) for b in button_ids(inter))
    for n in range(2, 5):
        tap("done")
        assert f"Langkah {n} dari 4" in last_interactive()["body"]["text"]
    n0 = len(fg.sent)
    tap("done")
    tail = sent_since(n0)
    assert [m["type"] for m in tail] == ["text", "document"]
    assert "Semua langkah selesai" in tail[0]["text"]["body"]
    doc = tail[-1]["document"]
    assert doc["filename"].endswith(".pdf")
    pdf = fg.uploads[doc["id"]]
    assert pdf["mime"] == "application/pdf" and pdf["data"][:4] == b"%PDF"
    assert any(c.startswith("POST media v26.0") for c in fg.calls) and any(c.startswith("GET media v26.0") for c in fg.calls)


def test_photo_with_caption_starts_at_once_in_english(samples):
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_EN))
    inter = last_interactive()
    assert "Step 1 of 4" in inter["body"]["text"]
    assert [b["reply"]["title"] for b in inter["action"]["buttons"]] == ["Done", "Problem", "Stop"]
    assert "Offline sample mode" in [m for m in fg.sent if m["type"] == "image"][0]["image"]["caption"]


def _ogg(tmp_path):
    out = tmp_path / "v.ogg"
    r = subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                        "sine=frequency=300:duration=1", "-ac", "1", "-c:a", "libopus", str(out)], capture_output=True)
    if r.returncode != 0:
        pytest.skip("ffmpeg without libopus")
    return out.read_bytes()


def test_voice_note_flow_with_follow_up_question(samples, tmp_path):
    deliver(fg.image_msg(PHONE, photo(samples, "motor")))
    assert fg.sent[-1]["text"]["body"] == wa_text.t("ask_text", "id")
    deliver(fg.audio_msg(PHONE, fg.add_media(_ogg(tmp_path), "audio/ogg; codecs=opus")))
    # the demo transcript is the motorbike that won't start: low confidence, so the engine asks one question
    assert fg.sent[-1]["type"] == "text" and fg.sent[-1]["text"]["body"].startswith("❓")
    s = engine.load(_sid())
    assert s["status"] == "needs_answer" and s["has_audio"] and not (engine.session_dir(s["id"]) / "voice.wav").exists()
    deliver(fg.text_msg(PHONE, "Busi kelihatan hitam dan basah"))
    assert "Langkah 1" in last_interactive()["body"]["text"]


def test_red_stop_in_javanese_before_any_photo():
    deliver(fg.text_msg(PHONE, GAS_JV))
    assert len(fg.sent) == 1
    body = fg.sent[0]["text"]["body"]
    assert "Dimandhegake kanggo keslametan" in body and "mbebayani" in body
    assert "google.com/maps" in body and "kompor+gas" in body and "112" in body
    assert "Langkah" not in body and not any(m["type"] == "interactive" for m in fg.sent)


def test_red_stop_after_photo_has_no_steps(samples):
    deliver(fg.image_msg(PHONE, photo(samples, "rice"), caption=RICE_ID))
    kinds = [m["type"] for m in fg.sent]
    assert "interactive" not in kinds and "document" not in kinds
    body = fg.sent[-1]["text"]["body"]
    assert "Dihentikan demi keselamatan" in body and "rice+cooker" in body and "Langkah" not in body


def test_problem_button_replans_and_old_buttons_go_stale(samples):
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID))
    old = button_ids(last_interactive())
    tap("problem")
    texts = [m["text"]["body"] for m in fg.sent if m["type"] == "text"]
    assert any(x.startswith("🔁 Rencana 2") for x in texts)
    new = button_ids(last_interactive())
    assert ":1:1" in new[0] and new != old and "Langkah 1" in last_interactive()["body"]["text"]
    deliver(fg.button_msg(PHONE, old[0], "Selesai"))
    assert last_interactive()["body"]["text"].startswith(wa_text.t("stale", "id"))


def test_still_broken_text_replans_too(samples):
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID))
    deliver(fg.text_msg(PHONE, "masih netes"))
    assert any(m["type"] == "text" and m["text"]["body"].startswith("🔁") for m in fg.sent)


def test_photo_during_a_step_runs_the_camera_check(samples):
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID))
    deliver(fg.image_msg(PHONE, fg.add_media(_jpg((5, 5, 5)), "image/jpeg")))  # too dark: fails
    body = last_interactive()["body"]["text"]
    assert body.startswith("❌") and "Langkah 1 dari 4" in body
    deliver(fg.image_msg(PHONE, photo(samples)))  # a clear photo passes and moves on
    body = last_interactive()["body"]["text"]
    assert body.startswith("✅") and "Langkah 2 dari 4" in body
    s = engine.load(_sid())
    assert s["checks"]["1"]["passed"] is True and s["checks_used"] == 2


def test_stop_button_sends_report_and_workshop(samples):
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID))
    n0 = len(fg.sent)
    tap("stop")
    tail = sent_since(n0)
    assert tail[0]["type"] == "text" and "google.com/maps" in tail[0]["text"]["body"]
    assert tail[-1]["type"] == "document"


def test_erase_deletes_the_repair_now(samples):
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID))
    sid = _sid()
    assert engine.session_dir(sid).exists()
    deliver(fg.text_msg(PHONE, "HAPUS"))
    assert not engine.session_dir(sid).exists()
    assert fg.sent[-1]["text"]["body"] == wa_text.t("erased", "id")


def test_unknown_message_types_get_a_polite_answer():
    m = {"from": PHONE, "id": "wamid.loc1", "timestamp": "1", "type": "location", "location": {"latitude": -6.9, "longitude": 110.4}}
    sticker = {"from": PHONE, "id": "wamid.st1", "timestamp": "1", "type": "sticker", "sticker": {"id": "1", "mime_type": "image/webp"}}
    reaction = {"from": PHONE, "id": "wamid.re1", "timestamp": "1", "type": "reaction", "reaction": {"message_id": "x", "emoji": "👍"}}
    deliver(m, sticker, reaction)
    assert [x["text"]["body"] for x in fg.sent] == [wa_text.t("unsupported", "id")] * 2


def test_unsupported_media_mime_and_too_big(samples, monkeypatch):
    deliver(fg.image_msg(PHONE, fg.add_media(b"GIF89a....", "image/gif"), mime="image/gif"))
    assert fg.sent[-1]["text"]["body"] == wa_text.t("unsupported", "id")
    monkeypatch.setattr(wa, "MAX_PHOTO", 1000)
    deliver(fg.image_msg(PHONE, photo(samples)))
    assert fg.sent[-1]["text"]["body"] == wa_text.t("too_big", "id")


def test_broken_photo_is_refused(samples):
    deliver(fg.image_msg(PHONE, fg.add_media(b"\xff\xd8 not really a jpeg", "image/jpeg")))
    assert fg.sent[-1]["text"]["body"] == wa_text.t("bad_photo", "id")


def test_long_text_is_refused():
    deliver(fg.text_msg(PHONE, "a" * 2001))
    assert fg.sent[-1]["text"]["body"] == wa_text.t("too_long", "id")


def test_logs_never_carry_the_token_or_full_number(samples, caplog):
    caplog.set_level(logging.DEBUG)
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID))
    text = caplog.text
    assert fg.TOKEN not in text and PHONE not in text
    assert wa.mask(PHONE) == "***890"


def test_album_photos_are_collected_before_starting(samples, monkeypatch):
    from api.settings import settings

    monkeypatch.setattr(settings, "wa_debounce_s", 0.3)
    deliver(fg.image_msg(PHONE, photo(samples), caption=FAUCET_ID), fg.image_msg(PHONE, photo(samples)))
    s = engine.load(_sid())
    assert len(s["photos"]) == 2 and s["status"] == "ready"


def test_expired_chats_are_dropped(samples):
    deliver(fg.image_msg(PHONE, photo(samples)))
    key = wa.user_key(PHONE)
    assert wa.conv_dir(key).exists()
    assert wa.cleanup(now=10**12) == 1
    assert key not in wa._convs and not wa.conv_dir(key).exists()


# --- language guess
@pytest.mark.parametrize("text,lang", [
    ("Motorku Honda Beat angel urip wiwit esuk, mung muni nanging mesine ora urip.", "jv"),
    ("Motor saya Honda Beat susah hidup dari pagi, tapi mesin nggak nyala.", "id"),
    ("My Honda Beat won't start since this morning.", "en"),
    (GAS_JV, "jv"),
    ("isih rusak", "jv"),
    ("masih rusak", "id"),
    ("kran wastafel", None),
])
def test_language_guess(text, lang):
    assert wa_text.detect(text) == lang


# --- simulator
CHAT = "0123456789abcdef0123"


def sim_poll(after=0):
    assert wa.wait_idle(30)
    return client.get("/api/wa-sim/poll", params={"chat": CHAT, "after": after}).json()


def test_simulator_runs_the_same_handler_in_javanese(samples):
    assert client.get("/api/wa-sim/info").json()["enabled"] is True
    r = client.post("/api/wa-sim/send", data={"chat": CHAT, "text": "Kran wastafel pawon netes terus senajan wis ditutup kenceng."},
                    files={"photo": ("a.jpg", samples["faucet"].read_bytes(), "image/jpeg")})
    assert r.status_code == 200
    msgs = [m["message"] for m in sim_poll()["messages"]]
    assert [m["type"] for m in msgs] == ["text", "image", "interactive"]
    assert [b["reply"]["title"] for b in msgs[-1]["interactive"]["action"]["buttons"]] == ["Rampung", "Ana masalah", "Mandheg"]
    mid = msgs[1]["image"]["id"]
    img = client.get(f"/api/wa-sim/media/{CHAT}/{mid}")
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"
    bid = msgs[-1]["interactive"]["action"]["buttons"][2]["reply"]["id"]
    client.post("/api/wa-sim/send", data={"chat": CHAT, "button": bid + "|Mandheg"})
    tail = [m["message"] for m in sim_poll(3)["messages"]]
    assert tail[-1]["type"] == "document"
    assert client.get(f"/api/wa-sim/media/{CHAT}/{tail[-1]['document']['id']}").content[:4] == b"%PDF"
    assert fg.sent == []  # the simulator never calls the Graph API


def test_simulator_red_stop_and_voice(tmp_path):
    client.post("/api/wa-sim/send", data={"chat": CHAT, "text": GAS_JV})
    body = sim_poll()["messages"][0]["message"]["text"]["body"]
    assert "keslametan" in body and "Langkah" not in body
    r = client.post("/api/wa-sim/send", data={"chat": CHAT}, files={"audio": ("v.ogg", _ogg(tmp_path), "audio/ogg")})
    assert r.status_code == 200
    assert sim_poll(1)["messages"][-1]["message"]["text"]["body"] == wa_text.t("ask_photo", "jv")


def test_simulator_input_checks(monkeypatch):
    from api.settings import settings

    assert client.post("/api/wa-sim/send", data={"chat": "NOT-A-CHAT", "text": "x"}).status_code == 400
    assert client.post("/api/wa-sim/send", data={"chat": CHAT}).status_code == 400
    assert client.get("/api/wa-sim/media/" + CHAT + "/../../etc").status_code == 404
    assert client.get("/api/wa-sim/sample/motor.jpg").status_code == 200
    assert client.get("/api/wa-sim/sample/secret.jpg").status_code == 404
    assert client.get("/wa").status_code == 200
    monkeypatch.setattr(settings, "mock", False)
    monkeypatch.setattr(settings, "meta_api_key", "k")
    monkeypatch.setattr(settings, "wa_sim", False)
    assert client.post("/api/wa-sim/send", data={"chat": CHAT, "text": "x"}).status_code == 404


def _sim_start_faucet(samples, text):
    client.post("/api/wa-sim/send", data={"chat": CHAT, "text": text},
                files={"photo": ("a.jpg", samples["faucet"].read_bytes(), "image/jpeg")})
    msgs = sim_poll()["messages"]
    assert msgs[-1]["message"]["type"] == "interactive"
    return msgs[-1]["seq"]


def _sim_sid() -> str:
    sid = wa._convs[wa_sim._key(CHAT)].sid
    assert sid
    return sid


@pytest.mark.parametrize("lang,text,step_word", [("id", FAUCET_ID, "Langkah"), ("jv", "Kran wastafel pawon netes terus senajan wis ditutup kenceng.", "Langkah"),
                                                 ("en", FAUCET_EN, "Step")])
def test_simulator_sample_after_photo_is_checked_on_the_step_it_shows(samples, lang, text, step_word):
    """The "after" button's photo (the dry spout) shows the plan's last step: the chat moves there, says so in the
    owner's language, and the check passes there instead of failing on step 1 (shut the valve)."""
    seq = _sim_start_faucet(samples, text)
    sid = _sim_sid()
    plan = engine.load(sid)["plan"]["steps"]
    from api import sample_step

    pick = sample_step.pick("faucet", plan)
    assert pick == {"n": len(plan), "shows": True}  # the dry spout is the last step of the demo plan
    after = client.get("/api/demo/check-photo/ok", params={"sample": "faucet"}).content
    r = client.post("/api/wa-sim/send", data={"chat": CHAT, "sample": "faucet"}, files={"photo": ("after.jpg", after, "image/jpeg")})
    assert r.status_code == 200
    first = sim_poll(seq)["messages"][0]["message"]
    body = first["text"]["body"] if first["type"] == "text" else first["interactive"]["body"]["text"]
    assert body.startswith(wa_text.t("sample_for", lang, n=pick["n"])) and "✅" in body
    s = engine.load(sid)
    assert s["checks"][str(pick["n"])]["passed"] is True and "1" not in s["checks"]


def test_simulator_own_photo_stays_on_the_current_step(samples):
    """Without the sample flag (an owner's own photo, or a dark one) the check runs on the step the chat is on."""
    seq = _sim_start_faucet(samples, FAUCET_ID)
    dark = client.get("/api/demo/check-photo/dark", params={"sample": "faucet"}).content
    client.post("/api/wa-sim/send", data={"chat": CHAT}, files={"photo": ("dark.jpg", dark, "image/jpeg")})
    body = sim_poll(seq)["messages"][-1]["message"]["interactive"]["body"]["text"]
    assert body.startswith("❌") and "Langkah 1 dari 4" in body
    assert wa_text.t("sample_for", "id", n=4) not in body
    assert list(engine.load(_sim_sid())["checks"]) == ["1"]


def test_simulator_sample_flag_is_checked_and_the_webhook_cannot_set_it(samples):
    after = client.get("/api/demo/check-photo/ok", params={"sample": "faucet"}).content
    r = client.post("/api/wa-sim/send", data={"chat": CHAT, "sample": "../secret"}, files={"photo": ("a.jpg", after, "image/jpeg")})
    assert r.status_code == 400
    ev = wa.parse_message({"from": PHONE, "id": "wamid.X", "type": "image", "sample": "faucet",
                           "image": {"id": "m1", "mime_type": "image/jpeg", "sample": "faucet"}})
    assert ev is not None and ev.sample_after == ""


def test_sample_to_step_falls_back_to_the_last_step_and_ignores_unknown_plans():
    conv = wa.Conv(key="k", sender="sim:k", lang="en")
    s = {"plan": {"steps": [{"n": 1, "expected_state": "Key off."}, {"n": 2, "expected_state": "Engine runs."}]}}
    conv.step = 1
    assert wa.sample_to_step(conv, s, "motor") == wa_text.t("sample_for_last", "en", n=2) and conv.step == 2
    conv.step = 1
    assert wa.sample_to_step(conv, s, "") == "" and conv.step == 1
    assert wa.sample_to_step(conv, {"plan": {"steps": []}}, "motor") == "" and conv.step == 1
