"""Run the real ShopMind Agent behind the local judge-facing frontend.

This is a presentation/dev bridge only. It imports the same `Agent` implementation used by the
submission/evaluator and never changes its scoring contract. The browser talks to this process over
localhost; no hosted service is involved.

Usage:
    python tools/run_frontend.py
Then open http://127.0.0.1:8765
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "index.html"
CATALOG = ROOT / "data" / "catalog.jsonl"

sys.path.insert(0, str(ROOT))

from src.copilot.agent import Agent  # noqa: E402
from src.copilot.strategy_config import as_dict as strategy_config  # noqa: E402

agent = Agent(str(CATALOG))
SESSIONS: dict[str, dict] = {}


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def product_view(pid: str) -> dict | None:
    p = agent.catalog_index.products.get(str(pid))
    if not p:
        return None
    details = p.get("details") if isinstance(p.get("details"), dict) else {}
    return {
        "parent_asin": str(p.get("parent_asin", pid)),
        "title": p.get("title") or "Untitled product",
        "price": p.get("price"),
        "average_rating": p.get("average_rating"),
        "rating_number": p.get("rating_number"),
        "store": p.get("store"),
        "categories": p.get("categories") or [],
        "features": p.get("features") or [],
        "description": p.get("description") or [],
        "details": details,
    }


def snapshot(session_id: str) -> dict:
    record = SESSIONS.get(session_id)
    if not record:
        return {"exists": False, "session_id": session_id}
    state = agent._sessions.get(session_id)
    if state is None:
        return {"exists": False, "session_id": session_id}
    last = record.get("last_response") or {}
    rec_ids = [str(x.get("parent_asin")) for x in last.get("recommendations", []) if isinstance(x, dict)]
    candidates = [str(x) for x in state.candidate_pool]
    return {
        "exists": True,
        "session_id": session_id,
        "turn": state.turn_count,
        "turns_remaining": max(0, state.turns_remaining),
        "track": "buying" if state.buying_intent_score >= 0.5 else "browsing",
        "buying_intent_score": round(float(state.buying_intent_score), 4),
        "slots": json_safe(state.slots),
        "slot_confidence": json_safe(state.slot_confidence),
        "rejected_hard": json_safe(state.rejected_hard),
        "rejected_soft": json_safe(state.rejected_soft),
        "rejected_soft_confidence": json_safe(state.rejected_soft_confidence),
        "override_history": json_safe(state.override_history),
        "accumulated_terms": json_safe(state.accumulated_terms),
        "candidate_pool": candidates,
        "candidate_pool_size": len(candidates),
        "pool_entropy": round(float(state.pool_entropy), 5),
        "last_asked_attribute": state.last_asked_attribute,
        "exhausted_attributes": sorted(state.exhausted_attributes),
        "last_response": json_safe(last),
        "recommendation_products": [p for p in (product_view(pid) for pid in rec_ids) if p],
        "config": strategy_config(),
        "agent_mode": "guaranteed-offline" if agent.llm_client is None else "optional-llm-enabled",
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ShopMindLocal/1.0"

    def _send(self, status: int, payload, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send(200, {"ok": True, "agent": "real", "catalog": str(CATALOG.name), "sessions": len(SESSIONS)})
            return
        if path == "/api/config":
            self._send(200, {"config": strategy_config(), "agent_mode": "guaranteed-offline" if agent.llm_client is None else "optional-llm-enabled"})
            return
        if path.startswith("/api/session/"):
            sid = path.rsplit("/", 1)[-1]
            self._send(200, snapshot(sid))
            return
        if path == "/" or path == "/index.html":
            try:
                self._send(200, FRONTEND.read_bytes(), "text/html")
            except OSError as exc:
                self._send(500, {"error": str(exc)})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:
            self._send(400, {"error": f"invalid JSON: {exc}"})
            return

        try:
            if path == "/api/reset":
                sid = str(body.get("session_id") or f"web_{uuid.uuid4().hex[:12]}")
                profile = body.get("user_profile") if isinstance(body.get("user_profile"), dict) else {}
                agent.reset(sid, profile)
                SESSIONS[sid] = {"created_at": time.time(), "messages": [], "last_response": None}
                self._send(200, snapshot(sid))
                return

            if path == "/api/respond":
                sid = str(body.get("session_id") or "")
                message = str(body.get("message") or "").strip()
                if not sid or sid not in SESSIONS:
                    self._send(400, {"error": "Unknown session. Call /api/reset first."})
                    return
                if not message:
                    self._send(400, {"error": "message is required"})
                    return
                state = agent._sessions.get(sid)
                next_turn = (state.turn_count + 1) if state else 1
                if next_turn > 10:
                    self._send(409, {"error": "The Agent contract caps a session at 10 turns.", "session": snapshot(sid)})
                    return
                top_k = max(1, min(10, int(body.get("top_k", 10))))
                started = time.perf_counter()
                response = agent.respond(sid, message, next_turn, top_k)
                elapsed_ms = (time.perf_counter() - started) * 1000
                SESSIONS[sid]["messages"].append({"role": "user", "content": message, "turn": next_turn})
                SESSIONS[sid]["messages"].append({"role": "assistant", "content": response.get("message", ""), "turn": next_turn, "ask_attribute": response.get("ask_attribute")})
                SESSIONS[sid]["last_response"] = response
                payload = snapshot(sid)
                payload["latency_ms"] = round(elapsed_ms, 1)
                payload["response"] = json_safe(response)
                payload["messages"] = SESSIONS[sid]["messages"]
                self._send(200, payload)
                return

            if path == "/api/export":
                sid = str(body.get("session_id") or "")
                if sid not in SESSIONS:
                    self._send(404, {"error": "unknown session"})
                    return
                self._send(200, snapshot(sid))
                return
        except Exception as exc:
            self._send(500, {"error": type(exc).__name__ + ": " + str(exc)})
            return
        self._send(404, {"error": "not found"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"ShopMind real-agent frontend: http://{args.host}:{args.port}")
    print(f"Catalog: {CATALOG}")
    print(f"Agent mode: {'guaranteed-offline' if agent.llm_client is None else 'optional-llm-enabled'}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
