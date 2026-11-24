"""SGO Phase-0: offline planning, MCP contract inspection and WAV verification.

No network, OAuth, paid tool execution or automatic publication. All MCP call
objects are proposals for a separately authorized client, never executed here.
"""
import argparse
import hashlib
import json
import math
import statistics
import struct
import sys
import wave
from pathlib import Path
from jsonschema import Draft202012Validator

ENDPOINT = "https://api.suno.com/mcp"
NAMES = ("account-usage", "audio-create", "audio-wait",
         "audio-retrieve", "audio-analysis", "audio-download")
MAX_JSON = 2_000_000

class ContractError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ContractError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def read_json(path):
    p = Path(path)
    require(p.stat().st_size <= MAX_JSON, "JSON exceeds local size limit")
    return json.loads(p.read_text(encoding="utf-8"))

def schema_check(schema, value):
    require(isinstance(schema, dict), "schema must be an object")
    # Remote references are forbidden: never fetch a schema over the network.
    def walk(v):
        if isinstance(v, dict):
            require(not any(k in v for k in ("$ref", "$dynamicRef", "$recursiveRef")),
                    "references require explicit local resolution; unsupported here")
            for item in v.values():
                walk(item)
        elif isinstance(v, list):
            for item in v:
                walk(item)
    walk(schema)
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(value))
    require(not errors, "input violates observed schema")

def tools_snapshot(pages):
    """Import all raw tools/list result pages from an authorized client.
    For a client that cannot export the raw results, remain in fixture mode.
    """
    require(isinstance(pages, list) and pages, "nonempty tools/list pages required")
    catalog = {}
    for i, page in enumerate(pages):
        require(isinstance(page, dict) and isinstance(page.get("tools"), list),
                "invalid tools/list result")
        require(bool(page.get("nextCursor")) == (i < len(pages)-1),
                "incomplete or inconsistent pagination")
        for tool in page["tools"]:
            require(isinstance(tool, dict), "invalid tool entry")
            name = tool.get("name")
            require(isinstance(name, str) and name and name not in catalog,
                    "invalid or duplicate tool name")
            schema = tool.get("inputSchema")
            require(isinstance(schema, dict), "inputSchema missing")
            catalog[name] = schema
    missing = [n for n in NAMES if n not in catalog]
    return {"endpoint": ENDPOINT, "schema_sha256": digest(canonical(catalog)),
            "missing": missing, "catalog": catalog}

def proposed_call(snapshot, name, arguments):
    require(name in NAMES and name in snapshot["catalog"], "capability unavailable")
    schema = snapshot["catalog"][name]
    props = schema.get("properties")
    require(isinstance(props, dict) and set(arguments) <= set(props),
            "unobserved argument; do not silently drop")
    schema_check(schema, arguments)
    return {"name": name, "arguments": arguments}

def lyric_text(handoff):
    require(handoff.get("contract_version") == "1.0.0", "handoff version unsupported")
    for key in ("song_id", "lyric_version_id", "language"):
        require(isinstance(handoff.get(key), str) and handoff[key].strip(),
                "handoff identifier missing")
    lyrics = handoff.get("lyrics_text")
    require(isinstance(lyrics, str) and lyrics.strip(), "missing lyric text")
    normalized = lyrics.replace("\r\n", "\n").replace("\r", "\n")
    require(digest(normalized.encode("utf-8")) == handoff.get("lyrics_sha256"),
            "lyric hash mismatch")
    return normalized

def integer(v, name, lower, upper):
    require(type(v) is int and lower <= v <= upper, name + " out of range")
    return v

def plan_create(snapshot, handoff, style, bpm, duration, run_id,
                approved_credits, estimated_upper, remaining, max_candidates,
                model=None, allowed_models=None, controls=None, advanced=False):
    """One proposal; cost/output bounds supplied by operator, never inferred.
    Not a live budget reservation. Reconfirm account usage before execution.
    """
    require(isinstance(style, str) and style.strip(), "style missing")
    require(isinstance(run_id, str) and run_id.strip(), "attempt identifier missing")
    integer(bpm, "bpm", 30, 300)
    integer(duration, "duration", 15, 360)
    integer(approved_credits, "approved_credits", 1, 1_000_000)
    integer(estimated_upper, "estimated_upper", 1, 1_000_000)
    integer(remaining, "remaining", 0, 1_000_000)
    # Observed interface made two outputs per call. Treat this as a provisional
    # admission bound; client/operator must confirm current output behavior.
    integer(max_candidates, "max_candidates", 2, 100)
    require(estimated_upper <= min(approved_credits, remaining), "budget insufficient")
    text = lyric_text(handoff)
    args = {"lyrics": text, "style": f"{style}, target tempo {bpm} BPM",
            "duration": duration, "duration_strict": False}
    if model is not None:
        require(isinstance(allowed_models, list) and model in allowed_models, "model not granted")
        args["model"] = model
    if controls is not None:
        require(advanced is True and isinstance(controls, dict) and controls, "advanced controls not granted")
        require(set(controls) <= {"style_influence", "weirdness", "variety"}, "unsupported controls for custom lyrics")
        for key, value in controls.items():
            if key == "variety":
                integer(value, key, 0, 4)
            else:
                require(type(value) in (int, float) and 0 <= value <= 1, "slider out of range")
        args["controls"] = controls.copy()
    # Stable for this attempt and exact input. New attempt needs a new run_id.
    args["idempotency_key"] = "sgo-" + digest(canonical([run_id, args]))
    call = proposed_call(snapshot, "audio-create", args)
    return {"execution": "PROPOSAL_ONLY", "requires_live_reconfirmation": True,
            "schema_sha256": snapshot["schema_sha256"],
            "lyric_sha256": handoff["lyrics_sha256"],
            "operator_supplied_credit_upper": estimated_upper,
            "candidate_limit": max_candidates, "call": call,
            "approval_fingerprint": digest(canonical([snapshot["schema_sha256"], call,
                                                      approved_credits, estimated_upper,
                                                      remaining, max_candidates]))}

def unwrap(result):
    """MCP CallToolResult: accept structuredContent or one JSON text block.
    No success inferred from prose; reject errors and ambiguous envelopes.
    """
    require(isinstance(result, dict), "invalid tool result")
    require(result.get("isError", False) is False, "tool reported error")
    if "structuredContent" in result:
        data = result["structuredContent"]
    elif set(result) == {"text"} and isinstance(result["text"], str):
        # Authorized ChatGPT connector host envelope, observed in read-only calls.
        data = json.loads(result["text"])
    else:
        blocks = result.get("content")
        require(isinstance(blocks, list) and len(blocks) == 1 and
                isinstance(blocks[0], dict) and blocks[0].get("type") == "text" and
                isinstance(blocks[0].get("text"), str), "ambiguous tool result")
        data = json.loads(blocks[0]["text"])
    require(isinstance(data, dict) and not data.get("error"), "invalid response data")
    return data

def candidate_ids(result, limit):
    data = unwrap(result)
    ids = data.get("clip_ids")
    require(isinstance(ids, list) and 0 < len(ids) <= limit and
            all(isinstance(i, str) and i.strip() for i in ids) and
            len(set(ids)) == len(ids), "unknown or unexpected candidate IDs; stop")
    return ids

def wait_calls(snapshot, ids):
    require(isinstance(ids, list) and ids and
            all(isinstance(i, str) and i.strip() for i in ids) and
            len(set(ids)) == len(ids), "invalid candidate IDs")
    schema = snapshot["catalog"].get("audio-wait", {})
    max_items = schema.get("properties", {}).get("ids", {}).get("maxItems", 12)
    integer(max_items, "wait batch limit", 1, 100)
    limit = min(12, max_items)
    return [proposed_call(snapshot, "audio-wait",
                         {"ids": ids[i:i+limit], "until": "complete"})
            for i in range(0, len(ids), limit)]

def download_probe(snapshot, clip_id):
    require(isinstance(clip_id, str) and clip_id.strip(), "invalid clip ID")
    # Never spend a download credit here. A requires_credit result stops.
    return proposed_call(snapshot, "audio-download",
                         {"id": clip_id, "format": "wav", "confirm": False})

def download_decision(result):
    data = unwrap(result)
    status = data.get("status")
    if status == "requires_credit":
        return "NEEDS_SEPARATE_APPROVAL"
    if status == "processing":
        return "WAIT_FOR_DOWNLOAD"
    # Do not persist credential-bearing URLs, or follow them from this CLI.
    if isinstance(data.get("url"), str) and data["url"].startswith("https://"):
        return "CLIENT_DOWNLOAD_OR_MANUAL_SAVE"
    return "UNKNOWN_STOP"

def wav_metrics(path):
    """Independent basic PCM16 WAV QA. Tempo estimator is for clear pulses,
    not a general beat tracker. Unknown for weak/irregular attacks.
    """
    p = Path(path)
    require(p.stat().st_size <= 256*1024*1024, "WAV exceeds local size limit")
    with wave.open(str(p), "rb") as w:
        channels, width, rate, frames = (w.getnchannels(), w.getsampwidth(),
                                        w.getframerate(), w.getnframes())
        require(width == 2 and channels in (1,2) and 8000 <= rate <= 96000 and
                frames > 0 and frames/rate <= 600, "unsupported PCM WAV")
        hop = max(1, rate//100)  # 10 ms
        energy = []
        peaks = 0
        count = 0
        while True:
            raw = w.readframes(hop)
            if not raw:
                break
            samples = struct.unpack("<" + "h"*(len(raw)//2), raw)
            count += len(samples)
            peaks += sum(abs(s) >= 32760 for s in samples)
            energy.append(math.sqrt(sum(s*s for s in samples)/len(samples)))
    require(count == frames*channels, "truncated WAV")
    onset = [max(0.0, b-a) for a,b in zip(energy, energy[1:])]
    maximum = max(onset, default=0)
    hits = []
    if maximum > 100:
        for i, v in enumerate(onset):
            if v >= 0.35*maximum and (not hits or i-hits[-1] >= 20):
                hits.append(i)
    intervals = [(b-a)*hop/rate for a,b in zip(hits,hits[1:])]
    tempo = None
    if len(intervals) >= 5:
        median = statistics.median(intervals)
        if 0.25 <= median <= 1.5 and sum(abs(v-median) <= .04*median
                                         for v in intervals)/len(intervals) >= .8:
            tempo = round(60/median, 2)
    return {"duration_seconds": frames/rate, "tempo_bpm": tempo,
            "near_full_scale_samples": peaks,
            "tempo_method": "pulse-onset-v0; unvalidated on real music",
            "tempo_requires_human_confirmation": True,
            "sha256": digest(p.read_bytes())}

def evaluate(metrics, target_bpm, tolerance, min_sec, max_sec, confirmed_tempo=False):
    integer(target_bpm, "target_bpm", 30, 300)
    integer(tolerance, "tolerance", 0, 100)
    require(0 < min_sec <= max_sec <= 600, "invalid duration range")
    tempo = metrics["tempo_bpm"]
    duration = metrics["duration_seconds"]
    rows = [{"id":"R-01", "value":tempo, "unit":"BPM",
             "status": "UNKNOWN" if tempo is None or not confirmed_tempo else
                       ("PASS" if abs(tempo-target_bpm) <= tolerance else "FAIL")},
            {"id":"R-02", "value":duration, "unit":"s",
             "status":"PASS" if min_sec <= duration <= max_sec else "FAIL"}]
    states = {row["status"] for row in rows}
    return {"mode":"LOCAL_WAV", "rows":rows, "overall":
            "FAIL" if "FAIL" in states else "UNKNOWN" if "UNKNOWN" in states else "PASS",
            "scope":"BPM and duration only; no full-song acceptance",
            "human_approval_required":True, "metrics":metrics}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect")
    p.add_argument("pages")
    p = sub.add_parser("plan")
    p.add_argument("pages"); p.add_argument("handoff")
    p.add_argument("--style", required=True); p.add_argument("--bpm", type=int, required=True)
    p.add_argument("--duration", type=int, required=True); p.add_argument("--attempt-id", required=True)
    p.add_argument("--approved-credits", type=int, required=True)
    p.add_argument("--estimated-upper", type=int, required=True)
    p.add_argument("--remaining", type=int, required=True)
    p.add_argument("--max-candidates", type=int, required=True)
    p.add_argument("--model")
    p.add_argument("--usage", help="private account-usage envelope for model and controls grants")
    p.add_argument("--controls", help="JSON object of requested sliders; no automatic defaults")
    p = sub.add_parser("wait-plan")
    p.add_argument("pages"); p.add_argument("result")
    p.add_argument("--max-candidates", type=int, required=True)
    p = sub.add_parser("download-plan")
    p.add_argument("pages"); p.add_argument("clip_id")
    p = sub.add_parser("evaluate")
    p.add_argument("wav"); p.add_argument("--bpm", type=int, required=True)
    p.add_argument("--tolerance", type=int, default=5)
    p.add_argument("--min-sec", type=float, required=True); p.add_argument("--max-sec", type=float, required=True)
    p.add_argument("--confirmed-tempo", action="store_true")
    a = parser.parse_args()
    try:
        if a.command == "inspect":
            s = tools_snapshot(read_json(a.pages))
            result = {k:v for k,v in s.items() if k != "catalog"}
            result["tool_names"] = sorted(s["catalog"])
        elif a.command == "plan":
            usage = unwrap(read_json(a.usage)) if a.usage else {}
            result = plan_create(tools_snapshot(read_json(a.pages)), read_json(a.handoff),
                                 a.style, a.bpm, a.duration, a.attempt_id,
                                 a.approved_credits, a.estimated_upper, a.remaining, a.max_candidates,
                                 model=a.model, allowed_models=usage.get("allowed_models"),
                                 controls=json.loads(a.controls) if a.controls else None,
                                 advanced="controls.advanced" in usage.get("features", []))
        elif a.command == "wait-plan":
            s = tools_snapshot(read_json(a.pages))
            result = wait_calls(s, candidate_ids(read_json(a.result), a.max_candidates))
        elif a.command == "download-plan":
            result = download_probe(tools_snapshot(read_json(a.pages)), a.clip_id)
        else:
            result = evaluate(wav_metrics(a.wav), a.bpm, a.tolerance, a.min_sec, a.max_sec,
                              a.confirmed_tempo)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, OSError, wave.Error, KeyError, TypeError) as exc:
        # Error details may include private inputs; keep console output generic.
        print("STOP: " + type(exc).__name__, file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
