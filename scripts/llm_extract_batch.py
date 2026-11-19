"""Structured event extraction from Telegram war-news posts with Claude Haiku 5.5 (Message Batches API).

Steps (run from the repo root, venv: .venv/bin/python):
    python scripts/llm_extract_batch.py prepare            # filter posts, parse Air Force summaries (no API calls)
    python scripts/llm_extract_batch.py probe              # 1 synchronous request: checks key + schema
    python scripts/llm_extract_batch.py submit --sample 200   # test batch on a random sample
    python scripts/llm_extract_batch.py submit             # all remaining posts
    python scripts/llm_extract_batch.py status             # progress of submitted batches
    python scripts/llm_extract_batch.py collect            # download results -> data/llm/events_llm.jsonl, cost report

The API key is read from .env (ANTHROPIC_API_KEY=...) or the environment.
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from pathlib import Path

import anthropic
import pandas as pd
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "telegram"
OUT = ROOT / "data" / "llm"
OUT.mkdir(parents=True, exist_ok=True)
SELECTED = OUT / "selected_posts.jsonl"
BATCHES = OUT / "batches.json"
EVENTS = OUT / "events_llm.jsonl"
AF_DAILY = OUT / "kpszsu_daily.csv"

MODEL = "claude-haiku-5-5"
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6  # standard $/token; batch = 50%
MAX_CHARS = 2500


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ---------------------------------------------------------------- Air Force summaries (regex)
MONTHS = {"січня": 1, "лютого": 2, "березня": 3, "квітня": 4, "травня": 5, "червня": 6, "липня": 7,
          "серпня": 8, "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12}
ORIGINS = r"(Орел|Курськ|Брянськ|Міллерово|Приморсько-Ахтарськ|Шаталове|Навля|Донецьк|Крим|Гвардійське|Чауда|Ростов|Бєлгород|Воронеж|Каспійськ|Енгельс|Оленья|Моздок|Таганрог|Липецьк|Саратов)"


def _int(m):
    return int(m.group(1)) if m else None


def parse_af_summary(text, dt):
    if not re.search(r"(збито|подавлено)", text, re.I) or not re.search(r"(противник|ворог)\w*\s+атакував", text, re.I):
        return None
    m = re.search(r"[Уу] ніч на (\d{1,2}) (\w+)", text)
    night = None
    if m and m.group(2) in MONTHS:
        y = dt.year - (1 if (MONTHS[m.group(2)] == 12 and dt.month == 1) else 0)
        night = f"{y:04d}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    # launch counts are between "атакував" and the shot-down sentence (the header "ЗБИТО/ПОДАВЛЕНО N" comes first)
    seg = re.search(r"атакував(.*?)(?:Повітряний напад|збито|подавлено|знищено|$)", text, flags=re.I | re.S)
    before_shot = seg.group(1) if seg else ""
    num = r"(\d+)(?:-\w{1,3})?"  # "131-м ударним", "145-ма ударними"
    drones = sum(int(x) for x in re.findall(num + r"\s+ударн\w*\s+(?:БпЛА|безпілотник)", before_shot))
    missiles = sum(int(x) for x in re.findall(num + r"\s+(?:[\w«»\"-]+\s+){0,3}ракет", before_shot))
    shot = re.search(r"ЗБИТО/ПОДАВЛЕНО\s+(\d+)", text) or re.search(r"збито(?:/подавлено)?\s+(\d+)", text, re.I)
    return {
        "night_of": night,
        "launched_total": _int(re.search(r"атакував\w*\s+(\d+)\s+засоб", text)),
        "launched_drones": drones or None,
        "launched_missiles": missiles or None,
        "shot_down_total": _int(shot),
        "hit_locations": _int(re.search(r"на (\d+) локаці", text)),
        "launch_origins": ", ".join(sorted(set(re.findall(ORIGINS, text)))) or None,
    }


# ---------------------------------------------------------------- keyword filter
KW = re.compile(r"(атак|удар|обстріл|ракет|шахед|shahed|бпла|дрон|балістик|кинджал|калібр|іскандер|\bкаб\b|загин|загибл|поранен|вбит|жертв|"
                r"влучан|вибух|приліт|нпз|нафтопереробн|аеродром|енергетик|підстанц|знеструм|блекаут|"
                r"переговор|перемир|трамп|trump|путін|зеленськ|санкці|саміт|ультиматум|"
                r"знищен|уражен|збито|ппо|тривог)", re.I)


def cmd_prepare(a):
    rows = []
    for p in sorted(RAW.glob("*.jsonl")):
        rows += [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    posts = (pd.DataFrame(rows).drop_duplicates(["channel", "post_id"])
             .assign(datetime=lambda d: pd.to_datetime(d["datetime"], utc=True)))
    posts["text"] = posts["text"].fillna("")
    print(posts.groupby("channel").size().to_string())

    af = []
    for r in posts[posts.channel == "kpszsu"].itertuples():
        x = parse_af_summary(r.text, r.datetime)
        if x:
            af.append({"post_id": r.post_id, "posted_at": r.datetime.isoformat(), "url": r.url, **x})
    af = pd.DataFrame(af)
    af.to_csv(AF_DAILY, index=False)
    print(f"Air Force summaries parsed: {len(af)} -> {AF_DAILY.relative_to(ROOT)}")

    news = posts[posts.channel.isin(["lachentyt", "ssternenko"]) & posts.text.str.len().gt(30)]
    news = news[news.text.str.contains(KW)]
    kp = posts[posts.channel == "kpszsu"]
    # regex-parsed summaries + older formats ("ЗНИЩЕНО 21 «ШАХЕД»") that the regex does not cover
    summaries = kp[kp.post_id.isin(af.post_id)
                   | (kp.text.str.contains(r"(?:збито|знищено|подавлено)", case=False) & kp.text.str.contains(r"\d{2,}"))]
    sel = pd.concat([news, summaries]).sort_values("datetime")
    with open(SELECTED, "w", encoding="utf-8") as f:
        for r in sel.itertuples():
            f.write(json.dumps({"channel": r.channel, "post_id": int(r.post_id), "datetime": r.datetime.isoformat(),
                                "url": r.url, "text": r.text[:MAX_CHARS]}, ensure_ascii=False) + "\n")
    chars = sel.text.str.len().clip(upper=MAX_CHARS).sum()
    print(f"Selected for LLM: {len(sel)} posts ({sel.channel.value_counts().to_dict()}), {chars/1e6:.1f}M chars")


# ---------------------------------------------------------------- request definition
OBLASTS = ["Вінницька", "Волинська", "Дніпропетровська", "Донецька", "Житомирська", "Закарпатська", "Запорізька",
           "Івано-Франківська", "Київська", "м. Київ", "Кіровоградська", "Луганська", "Львівська", "Миколаївська", "Одеська",
           "Полтавська", "Рівненська", "Сумська", "Тернопільська", "Харківська", "Херсонська", "Хмельницька", "Черкаська",
           "Чернівецька", "Чернігівська", "АР Крим", "м. Севастополь"]
INT_OR_NULL = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
SCHEMA = {
    "type": "object",
    "properties": {
        "relevant": {"type": "boolean"},
        "event_type": {"type": "string", "enum": ["russian_attack_on_ukraine", "ukrainian_strike_on_russia", "casualties_update",
                                                  "air_defense_summary", "diplomacy_politics", "frontline", "energy_outage", "other"]},
        "event_date": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "ua_oblasts": {"type": "array", "items": {"type": "string", "enum": OBLASTS}},
        "ru_regions": {"type": "array", "items": {"type": "string"}},
        "weapons": {"type": "array", "items": {"type": "string", "enum": [
            "shahed", "jet_shahed", "decoy_drone", "ballistic_missile", "cruise_missile", "kh22_onyx", "glide_bomb_kab",
            "artillery", "fpv_drone", "long_range_ua_drone", "other"]}},
        "launched": INT_OR_NULL, "shot_down": INT_OR_NULL,
        "killed": INT_OR_NULL, "injured": INT_OR_NULL, "children_killed": INT_OR_NULL,
        "target_type": {"type": "string", "enum": ["energy", "residential", "civil_infrastructure", "military",
                                                   "oil_refinery_or_depot", "airfield", "industry_defense", "transport", "unknown"]},
        "is_count_update": {"type": "boolean"},
        "actors": {"type": "array", "items": {"type": "string"}},
        "diplomacy_signal": {"type": "string", "enum": ["none", "peace_talks_positive", "peace_talks_negative",
                                                        "threat_or_ultimatum", "sanctions", "aid_to_ukraine"]},
        "summary_en": {"type": "string"},
    },
    "required": ["relevant", "event_type", "event_date", "ua_oblasts", "ru_regions", "weapons", "launched", "shot_down",
                 "killed", "injured", "children_killed", "target_type", "is_count_update", "actors", "diplomacy_signal",
                 "summary_en"],
    "additionalProperties": False,
}
SYSTEM = """You extract structured data from one Telegram post about the Russia-Ukraine war. Posts are in Ukrainian.
Return only facts stated explicitly in the post. Use null for any number that is not stated. Do not infer or estimate.

Field rules:
- relevant: false if the post is not about the war (then event_type = "other", lists empty, numbers null).
- event_type: the main subject. "air_defense_summary" = official overnight summary of launched/shot-down weapons.
  "casualties_update" = post mainly reports killed/injured after an attack.
  "ukrainian_strike_on_russia" = Ukrainian strikes on Russian territory or occupied Crimea.
- event_date: YYYY-MM-DD of the event, not of publication. Resolve "вчора", "сьогодні", "у ніч на" using the publication date.
- ua_oblasts: Ukrainian oblasts where strikes, hits or casualties happened (Kyiv city = "м. Київ").
- ru_regions: Russian regions or cities hit by Ukrainian strikes, as written in the post, in Ukrainian.
- launched / shot_down: totals of air-attack weapons for the event, if stated.
- killed / injured / children_killed: civilian casualties of this event. If the post updates an earlier count, give the new total and set is_count_update = true.
- actors: political figures or organisations whose statements or actions are reported (e.g. "Trump", "Putin", "Zelensky", "EU").
- diplomacy_signal: tone of diplomatic content, "none" if there is none.
- summary_en: one English sentence, at most 20 words."""


def make_params(post):
    return MessageCreateParamsNonStreaming(
        model=MODEL,
        max_tokens=1024,
        thinking={"type": "disabled"},
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content":
                   f"Channel: {post['channel']}\nPublished (UTC): {post['datetime'][:16]}\nPost:\n{post['text']}"}],
    )


def cid(post):
    return f"{post['channel']}-{post['post_id']}"


def read_selected():
    return [json.loads(l) for l in open(SELECTED, encoding="utf-8")]


def read_batches():
    return json.loads(BATCHES.read_text()) if BATCHES.exists() else []


def submitted_ids():
    ids = set()
    for b in read_batches():
        ids.update(b["custom_ids"])
    return ids


def cmd_probe(a):
    post = read_selected()[-1]
    client = anthropic.Anthropic()
    msg = client.messages.create(**make_params(post))
    print("stop_reason:", msg.stop_reason, "| usage:", msg.usage.input_tokens, "in /", msg.usage.output_tokens, "out")
    print(post["text"][:300], "\n->", next(b.text for b in msg.content if b.type == "text"))


def cmd_submit(a):
    posts = read_selected()
    done = submitted_ids()
    todo = [p for p in posts if cid(p) not in done]
    if a.sample:
        import random
        random.Random(42).shuffle(todo)
        todo = todo[:a.sample]
    if not todo:
        print("nothing to submit")
        return
    client = anthropic.Anthropic()
    for i in range(0, len(todo), 50_000):  # well below the 100k / 256 MB batch limits
        chunk = todo[i:i + 50_000]
        b = client.messages.batches.create(requests=[Request(custom_id=cid(p), params=make_params(p)) for p in chunk])
        rec = {"id": b.id, "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "n": len(chunk),
               "label": f"sample{a.sample}" if a.sample else "full", "custom_ids": [cid(p) for p in chunk]}
        BATCHES.write_text(json.dumps(read_batches() + [rec], indent=1))
        print(f"submitted {b.id}: {len(chunk)} requests")


def cmd_status(a):
    client = anthropic.Anthropic()
    for b in read_batches():
        s = client.messages.batches.retrieve(b["id"])
        c = s.request_counts
        print(f"{b['id']} [{b['label']}] {s.processing_status}: processing={c.processing} succeeded={c.succeeded} "
              f"errored={c.errored} expired={c.expired}")


def cmd_collect(a):
    client = anthropic.Anthropic()
    posts = {cid(p): p for p in read_selected()}
    have = set()
    if EVENTS.exists():
        have = {json.loads(l)["custom_id"] for l in open(EVENTS, encoding="utf-8")}
    tin = tcache = tout = n_new = n_err = 0
    with open(EVENTS, "a", encoding="utf-8") as f:
        for b in read_batches():
            if client.messages.batches.retrieve(b["id"]).processing_status != "ended":
                print(f"{b['id']} not finished yet, skipped")
                continue
            for r in client.messages.batches.results(b["id"]):
                if r.custom_id in have:
                    continue
                p = posts.get(r.custom_id, {})
                base = {"custom_id": r.custom_id, "channel": p.get("channel"), "post_id": p.get("post_id"),
                        "posted_at": p.get("datetime"), "url": p.get("url"), "model": MODEL}
                if r.result.type == "succeeded":
                    m = r.result.message
                    u = m.usage
                    tin += u.input_tokens
                    tcache += (u.cache_read_input_tokens or 0) * 0.1 + (u.cache_creation_input_tokens or 0) * 1.25
                    tout += u.output_tokens
                    try:
                        data = json.loads(next(x.text for x in m.content if x.type == "text"))
                        rec = {**base, **data, "stop_reason": m.stop_reason}
                    except Exception as e:
                        rec = {**base, "error": f"parse: {e!r}", "stop_reason": m.stop_reason}
                        n_err += 1
                else:
                    rec = {**base, "error": r.result.type}
                    n_err += 1
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                have.add(r.custom_id)
                n_new += 1
    cost = (tin + tcache) * PRICE_IN * 0.5 + tout * PRICE_OUT * 0.5  # tcache is weighted: read 0.1x, write 1.25x
    print(f"new results: {n_new} (errors {n_err}) -> {EVENTS.relative_to(ROOT)}")
    if n_new:
        print(f"tokens: in {tin:,} + cache {tcache:,}, out {tout:,}; batch cost ≈ ${cost:.3f} "
              f"(${cost / n_new * 1000:.3f} per 1k posts)")


def main():
    load_env()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("prepare")
    sp.add_parser("probe")
    s = sp.add_parser("submit")
    s.add_argument("--sample", type=int)
    sp.add_parser("status")
    sp.add_parser("collect")
    a = ap.parse_args()
    {"prepare": cmd_prepare, "probe": cmd_probe, "submit": cmd_submit, "status": cmd_status, "collect": cmd_collect}[a.cmd](a)


if __name__ == "__main__":
    main()
