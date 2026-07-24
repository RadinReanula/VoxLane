from pathlib import Path

from fastapi.testclient import TestClient

from voice_agent.app import create_app
from voice_agent.config import Settings


def test_mock_mode_order_flow_without_keys(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            mode="mock",
            database_url=f"sqlite+aiosqlite:///{tmp_path}/api.db",
            tax_rate="0",
        )
    )

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["mode"] == "mock"

        started = client.post("/v1/sessions")
        assert started.status_code == 201
        session_id = started.json()["session"]["id"]

        turn = client.post(
            f"/v1/sessions/{session_id}/turns",
            json={"schema_version": "1.0", "text": "add 2 cola"},
        )
        assert turn.status_code == 200
        assert turn.json()["order"]["total"] == "4.50"

        first = client.post(
            f"/v1/sessions/{session_id}/confirm",
            headers={"Idempotency-Key": "api-request-123"},
        )
        second = client.post(
            f"/v1/sessions/{session_id}/confirm",
            headers={"Idempotency-Key": "api-request-123"},
        )
        assert first.status_code == 200
        assert first.json() == second.json()

        handoff = client.post(
            f"/v1/sessions/{session_id}/handoff",
            json={"schema_version": "1.0", "reason": "operator"},
        )
        assert handoff.status_code == 200
        assert handoff.json()["status"] == "human_help"

        snapshot = client.get(f"/v1/sessions/{session_id}")
        assert snapshot.status_code == 200
        body = snapshot.json()
        assert body["session"]["id"] == session_id
        assert body["latest_sequence"] >= 1

        resumed = client.post(f"/v1/sessions/{session_id}/resume")
        assert resumed.status_code == 200
        assert resumed.json()["status"] == "active"

        caps = client.get("/v1/webrtc/capabilities")
        assert caps.status_code == 200
        assert "transport" in caps.json()
