import json
import subprocess
import sys
from pathlib import Path

from personal_knowledge.config import VaultConfig
from personal_knowledge.ingest import SourceWriteRequest, SourceWriter


def test_compile_source_cli_uses_concepts_file(tmp_path: Path):
    config_path = tmp_path / "vault.yaml"
    config_path.write_text(
        f"current_vault: {tmp_path / 'wiki'}\nstaging_vault: {tmp_path / 'staging'}\nproject_root: {tmp_path}\n",
        encoding="utf-8",
    )
    config = VaultConfig(vault_root=tmp_path / "wiki")
    source = SourceWriter(config).write(
        SourceWriteRequest(
            source_id="source_1",
            title="Agent Memory",
            body="# Agent Memory\n\nMemory hierarchy",
            source_type="article",
            domain_hint="ai",
        )
    )
    concepts_path = tmp_path / "concepts.json"
    concepts_path.write_text(
        json.dumps(
            [
                {
                    "title": "分层记忆系统",
                    "definition": "将记忆按生命周期分层。",
                    "summary": "短期和长期记忆承担不同任务。",
                    "related": ["上下文压缩"],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/compile_source.py",
            "--config",
            str(config_path),
            "--source",
            str(source.path),
            "--concepts",
            str(concepts_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "compiled"
    assert output["domain"] == "ai_agents"
    assert output["created_count"] == 1
    assert Path(output["created_paths"][0]).exists()
