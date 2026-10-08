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

"""GTK 4 / libadwaita compatibility for older distributions (e.g. Ubuntu 22.04).

TuxVox targets libadwaita 1.4+ (ToolbarView, AlertDialog). Jammy ships 1.1.x
and PyGObject may expose ``load_from_data`` but not ``load_from_string`` for
CSS. Patches are applied once at startup via :func:`apply_gtk_compat`.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


def css_provider_load_string(provider: Gtk.CssProvider, css: str) -> None:
    """Load CSS text into a :class:`Gtk.CssProvider`."""
    if hasattr(provider, "load_from_string"):
        provider.load_from_string(css)
    else:
        provider.load_from_data(css.encode("utf-8"))


def set_window_header_content(
    window: Adw.ApplicationWindow,
    header: Adw.HeaderBar,
    content: Gtk.Widget,
) -> None:
    """Attach a header bar and main content (ToolbarView or titlebar fallback)."""
    if hasattr(Adw, "ToolbarView"):
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        toolbar_view.set_content(content)
        window.set_content(toolbar_view)
    else:
        # AdwWindow does not support gtk_window_set_titlebar(); stack header + body.
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.append(header)
        content.set_vexpand(True)
        root.append(content)
        window.set_content(root)


class _LegacyAlertDialog:
    """Minimal stand-in for :class:`Adw.AlertDialog` on libadwaita < 1.2."""

    def __init__(self, heading: str, body: str) -> None:
        self._heading = heading
        self._body = body
        self._responses: list[tuple[str, str]] = []
        self._default: str | None = None
        self._close: str | None = None
        self._response_handler = None

    def add_response(self, response_id: str, label: str) -> None:
        self._responses.append((response_id, label))

    def set_response_appearance(self, _response_id: str, _appearance: object) -> None:
        return

    def set_default_response(self, response_id: str) -> None:
        self._default = response_id

    def set_close_response(self, response_id: str) -> None:
        self._close = response_id

    def connect(self, signal: str, callback) -> int:
        if signal == "response":
            self._response_handler = callback
            return 1
        return 0

    def present(self, parent: Gtk.Window | None) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            text=self._heading,
            secondary_text=self._body,
        )
        code_to_id: dict[int, str] = {}
        for index, (response_id, label) in enumerate(self._responses):
            code = index + 1
            code_to_id[code] = response_id
            dialog.add_button(label, code)

        default_code = next(
            (code for code, rid in code_to_id.items() if rid == self._default),
            None,
        )
        if default_code is not None:
            dialog.set_default_response(default_code)

        def _on_response(dlg: Gtk.MessageDialog, code: int) -> None:
            response_id = code_to_id.get(code, self._close or "")
            if self._response_handler is not None:
                self._response_handler(self, response_id)
            dlg.destroy()

        dialog.connect("response", _on_response)
        dialog.present()


class _AlertDialogType:
    @staticmethod
    def new(heading: str, body: str) -> _LegacyAlertDialog:
        return _LegacyAlertDialog(heading, body)


class _ResponseAppearanceType:
    DEFAULT = 0
    SUGGESTED = 1
    DESTRUCTIVE = 2


class SwitchRowCompat(Adw.ActionRow):
    """ActionRow + Gtk.Switch stand-in for :class:`Adw.SwitchRow` (libadwaita >= 1.4)."""

    def __init__(self, title: str = "", subtitle: str = "", **_kwargs: object) -> None:
        super().__init__()
        if title:
            self.set_title(title)
        if subtitle:
            self.set_subtitle(subtitle)
        self._switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.add_suffix(self._switch)
        self.set_activatable_widget(self._switch)

    def get_active(self) -> bool:
        return self._switch.get_active()

    def set_active(self, active: bool) -> None:
        self._switch.set_active(active)

    def connect(self, detailed_signal: str, handler) -> int:
        if detailed_signal == "notify::active":

            def _forward(_switch: Gtk.Switch, pspec) -> None:
                handler(self, pspec)

            return self._switch.connect("notify::active", _forward)
        return super().connect(detailed_signal, handler)


def apply_gtk_compat() -> None:
    """Install missing libadwaita symbols used by TuxVox on older systems."""
    if not hasattr(Adw, "ResponseAppearance"):
        Adw.ResponseAppearance = _ResponseAppearanceType  # type: ignore[attr-defined]

    if not hasattr(Adw, "AlertDialog"):
        Adw.AlertDialog = _AlertDialogType  # type: ignore[misc, assignment]

    if not hasattr(Adw, "SwitchRow"):
        Adw.SwitchRow = SwitchRowCompat  # type: ignore[misc, assignment]
