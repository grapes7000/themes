"""reload() must never hang or raise when a reload consumer stalls."""
import importlib.machinery
import importlib.util
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.sys.path.insert(0, str(ROOT / "bin"))
spec = importlib.util.spec_from_loader(
    "theme_reload_main",
    importlib.machinery.SourceFileLoader("theme_reload_main", str(ROOT / "bin/theme")),
)
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


def test_reload_survives_a_hanging_consumer():
    # dunstctl reload (and other reload consumers) have been observed to
    # hang indefinitely; reload() must bound every subprocess call so one
    # stuck consumer can't stall the whole theme switch.
    with patch.object(theme.subprocess, "run", side_effect=subprocess.TimeoutExpired(
            cmd=["dunstctl", "reload"], timeout=5)) as mock_run, \
         patch.object(theme.subprocess, "Popen") as mock_popen, \
         patch.dict(theme.os.environ, {}, clear=False):
        # Never let the test spawn a real hyprpaper process on this machine.
        theme.os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
        theme.reload(targets={})

    assert not mock_popen.called

    assert mock_run.called
    for call in mock_run.call_args_list:
        assert "timeout" in call.kwargs
        assert call.kwargs["timeout"] is not None
