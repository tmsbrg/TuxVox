# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""CLI helpers for controlling a running TuxVox instance."""

from __future__ import annotations

from pathlib import Path

TOGGLE_RECORDING_ARG = "--toggle-recording"


def get_toggle_recording_command() -> str:
    """Return a shell command that toggles experimental recording."""
    project_root = Path(__file__).resolve().parent.parent
    run_sh = project_root / "run.sh"
    if run_sh.is_file():
        return f"{run_sh} {TOGGLE_RECORDING_ARG}"
    return f"tuxvox {TOGGLE_RECORDING_ARG}"
