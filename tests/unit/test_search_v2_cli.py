import subprocess
import sys


def test_search_v2_help_imports_successfully():
    result = subprocess.run(
        [sys.executable, "scripts/search_v2.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 0
    assert "Search the V2 personal knowledge vault" in result.stdout
