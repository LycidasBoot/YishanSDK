from pathlib import Path

from agent.remote_log_agent import load_offset, save_offset


def test_remote_offset_round_trip(tmp_path: Path):
    offset_path = tmp_path / "offset.json"

    save_offset(offset_path, 123)

    assert load_offset(offset_path) == 123
