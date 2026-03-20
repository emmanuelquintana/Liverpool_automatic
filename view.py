# view.py
import tkinter as tk
from tkinter import filedialog
import threading
from datetime import datetime
import customtkinter as ctk
from pathlib import Path

from models import AppConfig
from viewmodel import LiverpoolViewModel, AUTO_SAVE_PATH
from dialogs import show_info, show_success, show_warning, show_error, show_confirm
from settings import save_settings

# NO llamar ctk.set_appearance_mode aquí — lo hace main.py con el valor guardado


def _timestamp() -> str:
    return datetime.now().strftime("[%H:%M:%S]")


def _play_done_sound():
    """Beep de notificación del sistema (Windows). Silencia si no está disponible."""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass


def _stats_msg(stats: dict) -> str:
    """Formatea las estadísticas de pedidos para mostrar en el modal."""
    lines = [
        f"✔  OK:        {stats['ok']}",
        f"✗  Errores:   {stats['error']}",
        f"⏭  Saltados:  {stats['skipped']}",
        f"─────────────────",
        f"Total: {stats['total']}",
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#  LiverpoolApp
# ══════════════════════════════════════════════════════════════════════

class LiverpoolApp(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.title("Liverpool Orders Automation")
        self.geometry("1000x800")

        self.config_obj = config
        self._operation_running = False

        self.vm = LiverpoolViewModel(self.config_obj)
        self.vm.set_log_callback(self.append_log)
        self.vm.set_progress_callback(self._on_progress)

        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)

        self.frames = {}
        for F in (MainScreen, ReprocessScreen):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame("MainScreen")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_frame(self, page_name):
        self.frames[page_name].tkraise()

    def append_log(self, msg: str):
        stamped = f"{_timestamp()} {msg}"
        self.after(0, self._dispatch_log, stamped)

    def _dispatch_log(self, stamped_msg: str):
        for frame in self.frames.values():
            if hasattr(frame, "append_log_screen"):
                frame.append_log_screen(stamped_msg)

    def _on_progress(self, current: int, total: int, label: str = ""):
        self.after(0, self._dispatch_progress, current, total, label)

    def _dispatch_progress(self, current: int, total: int, label: str):
        for frame in self.frames.values():
            if hasattr(frame, "update_progress"):
                frame.update_progress(current, total, label)

    def run_in_thread(self, fn, *args, on_finish=None):
        self._operation_running = True

        def _worker():
            error_ref = [None]
            try:
                fn(*args)
            except Exception as e:
                error_ref[0] = e
                self.append_log(f"[ERROR] {e}")
            finally:
                self._operation_running = False

                def _finish():
                    if error_ref[0] is not None:
                        show_error(self, "Error en la operación", str(error_ref[0]))
                    if on_finish:
                        on_finish()

                self.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_close(self):
        if self._operation_running:
            if show_confirm(
                self,
                "Cerrar aplicación",
                "Hay una operación en curso.\n¿Deseas cerrar de todas formas?\n(El navegador puede quedar abierto)",
            ):
                self.destroy()
        else:
            self.destroy()


# ══════════════════════════════════════════════════════════════════════
#  MainScreen
# ══════════════════════════════════════════════════════════════════════

class MainScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.vm = controller.vm
        self.selected_dates_vars = {}
        self._action_buttons: list = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header ──────────────────────────────────────────────────────
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.header_frame, text="Carpeta Base:", font=("Roboto Medium", 14)
        ).grid(row=0, column=0, padx=15, pady=15)

        self.base_dir_var = tk.StringVar(value=str(self.controller.config_obj.base_dir))
        ctk.CTkEntry(
            self.header_frame, textvariable=self.base_dir_var, height=35
        ).grid(row=0, column=1, sticky="ew", padx=10)

        ctk.CTkButton(
            self.header_frame, text="Elegir...", command=self.choose_base_dir,
            width=100, height=35,
        ).grid(row=0, column=2, padx=(0, 5))

        ctk.CTkButton(
            self.header_frame, text="Ir a Reprocesar JSON",
            command=lambda: self.controller.show_frame("ReprocessScreen"),
            fg_color="#8e44ad", hover_color="#732d91", width=150, height=35
        ).grid(row=0, column=3, padx=5)

        # Botón toggle tema 🌙 / ☀
        initial_icon = "☀" if ctk.get_appearance_mode() == "Light" else "🌙"
        self.btn_theme = ctk.CTkButton(
            self.header_frame, text=initial_icon, command=self._toggle_theme,
            width=40, height=35, font=("Segoe UI", 16),
            fg_color="transparent", hover_color="#333",
            border_width=1, border_color="#555",
        )
        self.btn_theme.grid(row=0, column=4, padx=(5, 15))

        # ── Panel central ────────────────────────────────────────────────
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(1, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)

        # ── Columna izquierda: Acciones ──────────────────────────────────
        self.actions_frame = ctk.CTkFrame(self.center_frame, corner_radius=10)
        self.actions_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.actions_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.actions_frame, text="Acciones", font=("Roboto Medium", 16)
        ).pack(pady=(15, 10))

        btn_params = {"height": 40, "font": ("Roboto", 13), "corner_radius": 8}

        self.btn_scan = ctk.CTkButton(
            self.actions_frame, text="1) Escanear Pedidos (Dry-run)",
            command=self.on_scan_click, fg_color="#2ecc71", hover_color="#27ae60", **btn_params)
        self.btn_scan.pack(fill="x", padx=20, pady=(10, 5))

        self.btn_process = ctk.CTkButton(
            self.actions_frame, text="2) Procesar Detalles",
            command=self.on_process_click, fg_color="#3498db", hover_color="#2980b9", **btn_params)
        self.btn_process.pack(fill="x", padx=20, pady=5)

        self.btn_accept = ctk.CTkButton(
            self.actions_frame, text="3) Aceptar y Descargar Guías",
            command=self.on_accept_click, fg_color="#e67e22", hover_color="#d35400", **btn_params)
        self.btn_accept.pack(fill="x", padx=20, pady=5)

        self.btn_auto_2_3 = ctk.CTkButton(
            self.actions_frame, text="2+3) Auto Procesar y Aceptar",
            command=self.on_auto_process_accept_click, fg_color="#D35400", hover_color="#A04000", **btn_params)
        self.btn_auto_2_3.pack(fill="x", padx=20, pady=5)

        self.btn_merge = ctk.CTkButton(
            self.actions_frame, text="4) Unir Guías PDF",
            command=self.on_merge_click, fg_color="#9b59b6", hover_color="#8e44ad", **btn_params)
        self.btn_merge.pack(fill="x", padx=20, pady=(5, 10))

        # ── Progreso + Cancelar ──────────────────────────────────────────
        prog_outer = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        prog_outer.pack(fill="x", padx=20, pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(prog_outer, height=8, corner_radius=4)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))

        prog_row = ctk.CTkFrame(prog_outer, fg_color="transparent")
        prog_row.pack(fill="x")
        prog_row.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            prog_row, text="Listo", font=("Roboto", 11), text_color="gray", anchor="w")
        self.progress_label.grid(row=0, column=0, sticky="w")

        self.btn_cancel = ctk.CTkButton(
            prog_row, text="⏹ Detener", command=self._on_cancel_click,
            fg_color="#c0392b", hover_color="#96281b",
            width=100, height=28, font=("Roboto", 11), corner_radius=6, state="disabled")
        self.btn_cancel.grid(row=0, column=1, padx=(10, 0))

        # ── Separador ────────────────────────────────────────────────────
        ctk.CTkFrame(self.actions_frame, height=2, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(
            self.actions_frame, text="Antiguos (hace 5 días)", font=("Roboto Medium", 14)
        ).pack(pady=(0, 5))

        self.btn_scan_old = ctk.CTkButton(
            self.actions_frame, text="5) Escanear Antiguos",
            command=self.on_scan_old_click, fg_color="#7f8c8d", hover_color="#95a5a6", **btn_params)
        self.btn_scan_old.pack(fill="x", padx=20, pady=5)

        self.btn_process_old = ctk.CTkButton(
            self.actions_frame, text="6) Procesar Antiguos",
            command=self.on_process_old_click, fg_color="#6c7a89", hover_color="#bdc3c7", **btn_params)
        self.btn_process_old.pack(fill="x", padx=20, pady=(5, 15))

        self._action_buttons = [
            self.btn_scan, self.btn_process, self.btn_accept,
            self.btn_auto_2_3, self.btn_merge, self.btn_scan_old, self.btn_process_old,
        ]

        # ── Columna derecha: Fechas ──────────────────────────────────────
        self.dates_container = ctk.CTkFrame(self.center_frame, corner_radius=10)
        self.dates_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.dates_container.grid_rowconfigure(2, weight=1)
        self.dates_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.dates_container, text="Fechas con Pendientes", font=("Roboto Medium", 16),
        ).grid(row=0, column=0, pady=(15, 8))

        sel_row = ctk.CTkFrame(self.dates_container, fg_color="transparent")
        sel_row.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 6))
        ctk.CTkButton(
            sel_row, text="✓ Todos", command=self._select_all_dates,
            width=80, height=26, font=("Roboto", 11),
            fg_color="#27ae60", hover_color="#1e8449", corner_radius=6
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            sel_row, text="✗ Ninguno", command=self._deselect_all_dates,
            width=80, height=26, font=("Roboto", 11),
            fg_color="#555", hover_color="#666", corner_radius=6
        ).pack(side="left")

        self.dates_scroll_frame = ctk.CTkScrollableFrame(
            self.dates_container, label_text="Selecciona fechas"
        )
        self.dates_scroll_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # ── Log ──────────────────────────────────────────────────────────
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header, text="Registro de Actividad", font=("Roboto Medium", 14)
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header, text="💾 Exportar", command=self._export_log,
            width=85, height=26, font=("Roboto", 11),
            fg_color="#2980b9", hover_color="#2471a3", corner_radius=6
        ).grid(row=0, column=1, sticky="e", padx=(0, 6))

        ctk.CTkButton(
            log_header, text="🗑 Limpiar", command=self._clear_log,
            width=80, height=26, font=("Roboto", 11),
            fg_color="#555", hover_color="#666", corner_radius=6
        ).grid(row=0, column=2, sticky="e")

        self.log_text = ctk.CTkTextbox(self.log_frame, height=150, font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            self, text="Desarrollado por Jose Emmanuel Quintana Torres",
            font=("Roboto", 10), text_color="gray",
        ).grid(row=3, column=0, pady=(0, 10))

    # ------------------------------------------------------------------
    # Helpers: estado, progreso, UI
    # ------------------------------------------------------------------

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self._action_buttons:
            btn.configure(state=state)

    def _run_action(self, action_fn, *args, post_ui=None):
        self._set_buttons_enabled(False)
        self.btn_cancel.configure(state="normal", text="⏹ Detener")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando...", text_color="gray")

        def _finish():
            self._set_buttons_enabled(True)
            self.btn_cancel.configure(state="disabled", text="⏹ Detener")
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="Completado ✔", text_color="#2ecc71")
            _play_done_sound()
            if post_ui:
                post_ui()

        self.controller.run_in_thread(action_fn, *args, on_finish=_finish)

    def update_progress(self, current: int, total: int, label: str = ""):
        if total > 0:
            self.progress_bar.set(current / total)
        txt = f"{label}  ({current}/{total})" if label else f"Procesando {current}/{total}"
        self.progress_label.configure(text=txt, text_color="white")

    def _on_cancel_click(self):
        self.vm.request_cancel()
        self.btn_cancel.configure(state="disabled", text="Cancelando...")
        self.progress_label.configure(text="Cancelando...", text_color="#e67e22")

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        save_settings({"appearance_mode": new_mode})
        self.btn_theme.configure(text="☀" if new_mode == "Light" else "🌙")

    def _select_all_dates(self):
        for var in self.selected_dates_vars.values():
            var.set(True)

    def _deselect_all_dates(self):
        for var in self.selected_dates_vars.values():
            var.set(False)

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _export_log(self):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filepath = filedialog.asksaveasfilename(
            title="Guardar log como...",
            defaultextension=".txt",
            initialfile=f"LOG_{ts}.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=str(self.controller.config_obj.base_dir),
        )
        if filepath:
            content = self.log_text.get("1.0", tk.END)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                show_success(self, "Log exportado", f"Guardado en:\n{filepath}")
            except Exception as e:
                show_error(self, "Error", f"No se pudo guardar el log:\n{e}")

    def _get_selected_dates(self) -> list:
        return [d for d, var in self.selected_dates_vars.items() if var.get()]

    def choose_base_dir(self):
        folder = filedialog.askdirectory(
            title="Selecciona carpeta base",
            initialdir=str(self.controller.config_obj.base_dir),
        )
        if folder:
            self.base_dir_var.set(folder)
            self.controller.config_obj.base_dir = Path(folder)
            save_settings({"base_dir": folder})
            show_info(self, "Carpeta actualizada", f"Carpeta base cambiada a:\n{folder}")

    def append_log_screen(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def refresh_dates_checkboxes(self):
        for widget in self.dates_scroll_frame.winfo_children():
            widget.destroy()
        self.selected_dates_vars.clear()

        dates_summary = self.vm.get_dates_summary()
        if not dates_summary:
            ctk.CTkLabel(
                self.dates_scroll_frame,
                text="(No hay fechas con pendientes)", text_color="gray",
            ).pack(anchor="w", pady=5)
            return

        for fecha, count in dates_summary:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                self.dates_scroll_frame,
                text=f"{fecha}  →  {count} pedidos",
                variable=var,
            )
            cb.pack(anchor="w", pady=5)
            self.selected_dates_vars[fecha] = var

    # ------------------------------------------------------------------
    # Handlers de botones
    # ------------------------------------------------------------------

    def on_scan_click(self):
        self.controller.append_log("=== Iniciando escaneo ===")

        def _do():
            self.vm.scan_orders()

        def _after():
            self.controller.after(0, self.refresh_dates_checkboxes)
            self.controller.append_log("=== Escaneo terminado ===")
            self.controller.after(
                0, lambda: show_success(
                    self, "Escaneo completado",
                    "Lista guardada automáticamente.\n(backup anterior en orders_auto_save.bak.json)"
                )
            )

        self._run_action(_do, post_ui=_after)

    def on_process_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para procesar.")
            return

        self.controller.append_log(
            f"=== Procesando detalles (dry-run) para fechas: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.vm.process_details_dry_run(selected_dates)

        def _after():
            self.controller.append_log("=== Proceso Fase 1 completado ===")
            stats = self.vm.get_batch_stats(selected_dates)
            msg = f"Detalles procesados.\n\n{_stats_msg(stats)}"
            self.controller.after(
                0, lambda: show_success(self, "Fase 1 completada", msg)
            )

        self._run_action(_do, post_ui=_after)

    def on_accept_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para aceptar/descargar guías.")
            return

        self.controller.append_log(
            f"=== Fase 2: Aceptar + descargar guías para: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.vm.accept_and_download_labels(selected_dates)

        def _after():
            self.controller.append_log("=== Proceso Fase 2 completado ===")
            stats = self.vm.get_batch_stats(selected_dates)
            msg = f"Guías descargadas.\n\n{_stats_msg(stats)}"
            self.controller.after(
                0, lambda: show_success(self, "Fase 2 completada", msg)
            )

        self._run_action(_do, post_ui=_after)

    def on_auto_process_accept_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para el proceso automático.")
            return

        self.controller.append_log(
            f"=== PROCESO AUTOMÁTICO (2+3) para: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.controller.append_log("--- [Auto] Paso 1: Procesar Detalles ---")
            self.vm.process_details_dry_run(selected_dates)
            self.controller.append_log("--- [Auto] Paso 2: Aceptar y Descargar ---")
            self.vm.accept_and_download_labels(selected_dates)

        def _after():
            self.controller.append_log("=== PROCESO AUTOMÁTICO COMPLETADO ===")
            stats = self.vm.get_batch_stats(selected_dates)
            msg = f"Fases 2 y 3 ejecutadas correctamente.\n\n{_stats_msg(stats)}"
            self.controller.after(
                0, lambda: show_success(self, "Proceso automático completado", msg)
            )

        self._run_action(_do, post_ui=_after)

    def on_merge_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para unir guías.")
            return

        self.controller.append_log(
            f"=== Fase 3: Uniendo guías para: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.vm.merge_labels(selected_dates)

        def _after():
            self.controller.append_log("=== Fase 3 completada ===")
            self.controller.after(
                0, lambda: show_success(
                    self, "Guías unidas",
                    "PDF unificado generado.\nRevisa GUIAS_<fecha>.pdf en la carpeta del día.",
                )
            )

        self._run_action(_do, post_ui=_after)

    def on_scan_old_click(self):
        self.controller.append_log("=== Escaneando pedidos antiguos (5 días antes) ===")
        result_holder = [None]

        def _do_wrapper():
            result_holder[0] = self.vm.scan_old_orders_5_days_ago()

        def _after():
            self.controller.after(0, self.refresh_dates_checkboxes)
            date_str = result_holder[0] or "?"
            self.controller.append_log(f"=== Escaneo de antiguos ({date_str}) finalizado ===")
            self.controller.after(
                0, lambda: show_success(self, "Escaneo completado", f"Pedidos antiguos en:\n{date_str}")
            )

        self._run_action(_do_wrapper, post_ui=_after)

    def on_process_old_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para procesar antiguos.")
            return

        self.controller.append_log(f"=== Procesando Antiguos para: {', '.join(selected_dates)} ===")

        def _do():
            self.vm.process_old_orders_execution(selected_dates)

        def _after():
            self.controller.append_log("=== Proceso de Antiguos completado ===")
            stats = self.vm.get_batch_stats(selected_dates)
            msg = f"Screenshots y guías procesadas.\n\n{_stats_msg(stats)}"
            self.controller.after(
                0, lambda: show_success(self, "Proceso de antiguos completado", msg)
            )

        self._run_action(_do, post_ui=_after)


# ══════════════════════════════════════════════════════════════════════
#  ReprocessScreen
# ══════════════════════════════════════════════════════════════════════

class ReprocessScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.vm = controller.vm
        self.selected_dates_vars = {}
        self._action_buttons: list = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ──────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, corner_radius=10)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(
            self.header,
            text="Reprocesar Lista Guardada (Sin Validar Estado)",
            font=("Roboto Medium", 18)
        ).pack(pady=10)

        self.btns_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.btns_frame.pack(fill="x", padx=20, pady=(0, 5))

        self.btn_load_last = ctk.CTkButton(
            self.btns_frame, text="⚡ Cargar último guardado",
            command=self.on_load_last_saved,
            fg_color="#16a085", hover_color="#1abc9c",
        )
        self.btn_load_last.pack(side="left", padx=(0, 6))

        self.btn_load = ctk.CTkButton(
            self.btns_frame, text="📂 Cargar JSON",
            command=self.on_load_json,
            fg_color="#f39c12", hover_color="#e67e22"
        )
        self.btn_load.pack(side="left", padx=(0, 6))

        self.btn_run_reprocess = ctk.CTkButton(
            self.btns_frame, text="Ejecutar Reproceso",
            command=self.on_run_reprocess,
            fg_color="#e74c3c", hover_color="#c0392b"
        )
        self.btn_run_reprocess.pack(side="left", padx=(0, 6))

        self.btn_back = ctk.CTkButton(
            self.btns_frame, text="← Volver",
            command=lambda: self.controller.show_frame("MainScreen"),
            fg_color="gray"
        )
        self.btn_back.pack(side="right", padx=10)

        self._action_buttons = [self.btn_load_last, self.btn_load, self.btn_run_reprocess]

        # ── Progreso + Cancelar ──────────────────────────────────────────
        prog_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        prog_frame.pack(fill="x", padx=20, pady=(5, 10))

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=8, corner_radius=4)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))

        prog_row = ctk.CTkFrame(prog_frame, fg_color="transparent")
        prog_row.pack(fill="x")
        prog_row.grid_columnconfigure(0, weight=1)

        self.progress_label = ctk.CTkLabel(
            prog_row, text="Listo", font=("Roboto", 11), text_color="gray", anchor="w")
        self.progress_label.grid(row=0, column=0, sticky="w")

        self.btn_cancel = ctk.CTkButton(
            prog_row, text="⏹ Detener", command=self._on_cancel_click,
            fg_color="#c0392b", hover_color="#96281b",
            width=100, height=28, font=("Roboto", 11), corner_radius=6, state="disabled")
        self.btn_cancel.grid(row=0, column=1, padx=(10, 0))

        # ── Lista de fechas ──────────────────────────────────────────────
        self.mid_frame = ctk.CTkFrame(self)
        self.mid_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.mid_frame.grid_rowconfigure(1, weight=1)
        self.mid_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.mid_frame, text="Fechas en archivo cargado:", font=("Roboto Medium", 14)
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.dates_scroll = ctk.CTkScrollableFrame(self.mid_frame, height=200)
        self.dates_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # ── Log ──────────────────────────────────────────────────────────
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header, text="Registro de Actividad", font=("Roboto Medium", 14)
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header, text="💾 Exportar", command=self._export_log,
            width=85, height=26, font=("Roboto", 11),
            fg_color="#2980b9", hover_color="#2471a3", corner_radius=6
        ).grid(row=0, column=1, sticky="e", padx=(0, 6))

        ctk.CTkButton(
            log_header, text="🗑 Limpiar", command=self._clear_log,
            width=80, height=26, font=("Roboto", 11),
            fg_color="#555", hover_color="#666", corner_radius=6
        ).grid(row=0, column=2, sticky="e")

        self.log_text = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self._action_buttons:
            btn.configure(state=state)

    def update_progress(self, current: int, total: int, label: str = ""):
        if total > 0:
            self.progress_bar.set(current / total)
        txt = f"{label}  ({current}/{total})" if label else f"Procesando {current}/{total}"
        self.progress_label.configure(text=txt, text_color="white")

    def _on_cancel_click(self):
        self.vm.request_cancel()
        self.btn_cancel.configure(state="disabled", text="Cancelando...")
        self.progress_label.configure(text="Cancelando...", text_color="#e67e22")

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _export_log(self):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filepath = filedialog.asksaveasfilename(
            title="Guardar log como...",
            defaultextension=".txt",
            initialfile=f"LOG_{ts}.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filepath:
            content = self.log_text.get("1.0", tk.END)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                show_success(self, "Log exportado", f"Guardado en:\n{filepath}")
            except Exception as e:
                show_error(self, "Error", f"No se pudo guardar el log:\n{e}")

    def append_log_screen(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def on_load_last_saved(self):
        """Carga directamente el último orders_auto_save.json sin diálogo."""
        import os
        if not os.path.exists(AUTO_SAVE_PATH):
            show_warning(self, "Archivo no encontrado",
                         f"No existe el archivo auto-guardado:\n{AUTO_SAVE_PATH}")
            return
        try:
            self.controller.append_log(f"Cargando último guardado: {AUTO_SAVE_PATH}")
            self.vm.load_orders_json(AUTO_SAVE_PATH)
            self._refresh_dates()
            show_success(self, "Carga exitosa", "Último auto-guardado cargado correctamente.")
        except Exception as e:
            show_error(self, "Error de carga", f"No se pudo cargar el archivo:\n{e}")

    def on_load_json(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo JSON de pedidos",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            self.controller.append_log(f"Cargando pedidos de: {filepath}")
            self.vm.load_orders_json(filepath)
            self._refresh_dates()
            show_success(self, "Carga exitosa", "Se han cargado los pedidos del archivo JSON.")
        except Exception as e:
            show_error(self, "Error de carga", f"No se pudo cargar el archivo:\n{e}")

    def _refresh_dates(self):
        for w in self.dates_scroll.winfo_children():
            w.destroy()
        self.selected_dates_vars.clear()

        summary = self.vm.get_dates_summary()
        if not summary:
            ctk.CTkLabel(self.dates_scroll, text="No hay pedidos cargados.").pack()
            return

        for fecha, count in summary:
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                self.dates_scroll,
                text=f"{fecha} ({count} pedidos)",
                variable=var
            )
            cb.pack(anchor="w", pady=2)
            self.selected_dates_vars[fecha] = var

    def on_run_reprocess(self):
        selected = [d for d, var in self.selected_dates_vars.items() if var.get()]
        if not selected:
            show_warning(self, "Sin fechas", "Selecciona fechas para reprocesar.")
            return

        self.controller.append_log(f"Iniciando REPROCESO para: {len(selected)} fechas.")
        self._set_buttons_enabled(False)
        self.btn_cancel.configure(state="normal", text="⏹ Detener")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando...", text_color="gray")

        def _do():
            self.vm.reprocess_orders_json(selected)

        def _finish():
            self._set_buttons_enabled(True)
            self.btn_cancel.configure(state="disabled", text="⏹ Detener")
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="Completado ✔", text_color="#2ecc71")
            _play_done_sound()
            self.controller.append_log("Reproceso completado.")
            stats = self.vm.get_batch_stats(selected)
            msg = f"Pedidos reprocesados.\n\n{_stats_msg(stats)}"
            self.controller.after(
                0, lambda: show_success(self, "Reproceso completado", msg)
            )

        self.controller.run_in_thread(_do, on_finish=_finish)
