import os
import time

from app.core.config import Settings
from app.services.storage import objects
from app.services.storage.lifecycle import run_object_storage_lifecycle


def lifecycle_settings(tmp_path, **overrides) -> Settings:
    defaults = {
        "report_artifact_dir": str(tmp_path / "reports"),
        "equipment_file_dir": str(tmp_path / "equipment"),
        "travel_receipt_file_dir": str(tmp_path / "travel-receipts"),
        "travel_checklist_file_dir": str(tmp_path / "travel-checklists"),
        "travel_manifest_file_dir": str(tmp_path / "travel-manifests"),
        "safeguarding_incident_evidence_dir": str(tmp_path / "incident-evidence"),
        "safeguarding_incident_artifact_dir": str(tmp_path / "incident-artifacts"),
        "performance_video_file_dir": str(tmp_path / "performance-videos"),
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_object_storage_lifecycle_prunes_old_local_objects(tmp_path) -> None:
    settings = lifecycle_settings(tmp_path, object_storage_lifecycle_retention_days=30)
    old_report = tmp_path / "reports" / "org-1" / "old.pdf"
    old_equipment = tmp_path / "equipment" / "club-1" / "old-photo.jpg"
    fresh_report = tmp_path / "reports" / "org-1" / "fresh.pdf"
    for path in [old_report, old_equipment, fresh_report]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"artifact")
    old_timestamp = time.time() - 60 * 24 * 60 * 60
    for path in [old_report, old_equipment]:
        path.touch()
        path.chmod(0o644)
        time_tuple = (old_timestamp, old_timestamp)
        os.utime(path, time_tuple)

    dry_run = run_object_storage_lifecycle(settings, dry_run=True)
    assert dry_run["mode"] == "local"
    assert dry_run["eligible_count"] == 2
    assert dry_run["deleted_count"] == 0
    assert old_report.exists()

    result = run_object_storage_lifecycle(settings)
    assert result["eligible_count"] == 2
    assert result["deleted_count"] == 2
    assert result["deleted_bytes"] == len(b"artifact") * 2
    assert not old_report.exists()
    assert not old_equipment.exists()
    assert fresh_report.exists()


def test_object_storage_lifecycle_configures_s3_policy(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200
        text = ""

    def fake_put(url, *, content, headers, timeout):
        captured["url"] = url
        captured["content"] = content.decode()
        captured["headers"] = headers
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(objects.httpx, "put", fake_put)
    settings = lifecycle_settings(
        tmp_path,
        object_storage_mode="s3",
        object_storage_endpoint="http://minio.local:9000",
        object_storage_bucket="afrolete",
        object_storage_region="us-east-1",
        object_storage_access_key="access",
        object_storage_secret_key="secret",
        object_storage_lifecycle_retention_days=90,
        object_storage_lifecycle_prefixes=["reports/", "performance-videos/"],
    )

    result = run_object_storage_lifecycle(settings)

    assert result["mode"] == "s3"
    assert result["processed_count"] == 2
    assert captured["url"] == "http://minio.local:9000/afrolete?lifecycle="
    assert "reports/" in str(captured["content"])
    assert "performance-videos/" in str(captured["content"])
    assert "<Days>90</Days>" in str(captured["content"])
    assert "authorization" in captured["headers"]
