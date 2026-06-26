import json
import subprocess
import sys
from pathlib import Path


def test_ingest_source_cli_writes_source(tmp_path: Path):
    config_path = tmp_path / "vault.yaml"
    payload_path = tmp_path / "payload.json"
    config_path.write_text(
        f"current_vault: {tmp_path / 'wiki'}\nstaging_vault: {tmp_path / 'staging'}\nproject_root: {tmp_path}\n",
        encoding="utf-8",
    )
    payload_path.write_text(
        json.dumps(
            {
                "source_id": "task_123",
                "title": "AI Report",
                "body": "# Report\n\nUseful content",
                "source_type": "research_report",
                "domain_hint": "ai",
                "tags": ["AI"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ingest_source.py", "--config", str(config_path), "--payload", str(payload_path)],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "created"
    assert Path(output["path"]).exists()
