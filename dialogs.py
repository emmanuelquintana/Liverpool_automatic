# dialogs.py
"""
Modales personalizados con CustomTkinter para reemplazar los messagebox nativos.
Uso:
    from dialogs import show_info, show_warning, show_error, show_confirm
    show_info(parent, "Título", "Mensaje")
    ok = show_confirm(parent, "¿Continuar?", "¿Estás seguro?")
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional


# ──────────────────────────────────────────────
#  Paleta de colores para cada tipo de modal
# ──────────────────────────────────────────────
_STYLES = {
    "info": {
        "accent":   "#3498db",   # azul
        "icon":     "ℹ",
        "btn_ok":   "#3498db",
        "btn_ok_h": "#2980b9",
    },
    "success": {
        "accent":   "#2ecc71",   # verde
        "icon":     "✔",
        "btn_ok":   "#2ecc71",
        "btn_ok_h": "#27ae60",
    },
    "warning": {
        "accent":   "#e67e22",   # naranja
        "icon":     "⚠",
        "btn_ok":   "#e67e22",
        "btn_ok_h": "#d35400",
    },
    "error": {
        "accent":   "#e74c3c",   # rojo
        "icon":     "✖",
        "btn_ok":   "#e74c3c",
        "btn_ok_h": "#c0392b",
    },
}


class _BaseDialog(ctk.CTkToplevel):
    """
    Ventana modal base.  Las subclases sólo eligen el estilo y los botones.
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        style: str = "info",
        confirm: bool = False,   # True → muestra botón Cancelar
    ):
        super().__init__(parent)

        self._result: Optional[bool] = None
        style_cfg = _STYLES.get(style, _STYLES["info"])

        # ── Ventana ──────────────────────────────────────────
        self.title(title)
        self.resizable(False, False)
        self.grab_set()          # modal
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # ── Barra de acento lateral ───────────────────────────
        accent_bar = ctk.CTkFrame(self, width=6, fg_color=style_cfg["accent"], corner_radius=0)
        accent_bar.pack(side="left", fill="y")

        # ── Contenido principal ───────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True, padx=(16, 20), pady=20)

        # Fila superior: icono + título
        top_row = ctk.CTkFrame(main, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_row,
            text=style_cfg["icon"],
            font=("Segoe UI", 26),
            text_color=style_cfg["accent"],
            width=36,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_row,
            text=title,
            font=("Roboto Medium", 16),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Separador
        ctk.CTkFrame(main, height=1, fg_color="#444").pack(fill="x", pady=(0, 12))

        # Mensaje
        ctk.CTkLabel(
            main,
            text=message,
            font=("Roboto", 13),
            wraplength=380,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 20))

        # Botones
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x")

        if confirm:
            ctk.CTkButton(
                btn_row,
                text="Cancelar",
                command=self._on_cancel,
                fg_color="#555",
                hover_color="#666",
                width=110,
                height=36,
                font=("Roboto", 13),
                corner_radius=8,
            ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Aceptar",
            command=self._on_ok,
            fg_color=style_cfg["btn_ok"],
            hover_color=style_cfg["btn_ok_h"],
            width=110,
            height=36,
            font=("Roboto Medium", 13),
            corner_radius=8,
        ).pack(side="right")

        # ── Centrar sobre el padre ────────────────────────────
        self.update_idletasks()
        self._center(parent)

    def _center(self, parent):
        dw = self.winfo_width()
        dh = self.winfo_height()

        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except Exception:
            # fallback: centrar en pantalla
            px = (self.winfo_screenwidth() - dw) // 2
            py = (self.winfo_screenheight() - dh) // 2
            self.geometry(f"+{px}+{py}")
            return

        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _on_ok(self):
        self._result = True
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self._result = False
        self.grab_release()
        self.destroy()

    def get_result(self) -> Optional[bool]:
        return self._result


# ──────────────────────────────────────────────
#  Funciones de conveniencia (API pública)
# ──────────────────────────────────────────────

def _show(parent, title: str, message: str, style: str, confirm: bool = False) -> Optional[bool]:
    """Muestra el diálogo y espera a que se cierre (bloqueante)."""
    dlg = _BaseDialog(parent, title, message, style=style, confirm=confirm)
    parent.wait_window(dlg)
    return dlg.get_result()


def show_info(parent, title: str, message: str):
    _show(parent, title, message, style="info")


def show_success(parent, title: str, message: str):
    _show(parent, title, message, style="success")


def show_warning(parent, title: str, message: str):
    _show(parent, title, message, style="warning")


def show_error(parent, title: str, message: str):
    _show(parent, title, message, style="error")


def show_confirm(parent, title: str, message: str) -> bool:
    """Devuelve True si el usuario hizo clic en Aceptar, False si Cancelar o cerró."""
    return bool(_show(parent, title, message, style="warning", confirm=True))
