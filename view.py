# view.py
import tkinter as tk
from tkinter import filedialog
import threading
from datetime import datetime
import customtkinter as ctk
from pathlib import Path

from models import AppConfig
from viewmodel import LiverpoolViewModel
from dialogs import show_info, show_success, show_warning, show_error, show_confirm

# Configuración global de CustomTkinter
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


def _timestamp() -> str:
    """Devuelve la hora actual formateada para el log: [HH:MM:SS]"""
    return datetime.now().strftime("[%H:%M:%S]")


class LiverpoolApp(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.title("Liverpool Orders Automation")
        self.geometry("1000x800")

        self.config_obj = config
        self.vm = LiverpoolViewModel(self.config_obj)
        self.vm.set_log_callback(self.append_log)

        # Contenedor principal para cambiar de pantallas
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

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def append_log(self, msg: str):
        """Envía log (con timestamp) a todas las pantallas que tengan el método."""
        stamped = f"{_timestamp()} {msg}"
        # Se ejecuta siempre desde el hilo principal via after() para thread safety
        self.after(0, self._dispatch_log, stamped)

    def _dispatch_log(self, stamped_msg: str):
        for frame in self.frames.values():
            if hasattr(frame, "append_log_screen"):
                frame.append_log_screen(stamped_msg)

    def run_in_thread(self, fn, *args, on_finish=None):
        """
        Ejecuta 'fn(*args)' en un hilo de fondo.
        'on_finish' es un callable opcional que se llama en el hilo principal al terminar.
        """
        def _worker():
            try:
                fn(*args)
            except Exception as e:
                self.append_log(f"[ERROR] {e}")
            finally:
                if on_finish:
                    self.after(0, on_finish)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()


class MainScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.vm = controller.vm
        self.selected_dates_vars = {}
        self._action_buttons: list = []  # lista de botones a deshabilitar

        self._build_ui()

    def _build_ui(self):
        # --- Layout Principal ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # El contenido principal se expande

        # 1. Header / Configuración
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.lbl_base_dir = ctk.CTkLabel(
            self.header_frame, text="Carpeta Base:", font=("Roboto Medium", 14)
        )
        self.lbl_base_dir.grid(row=0, column=0, padx=15, pady=15)

        self.base_dir_var = tk.StringVar(value=str(self.controller.config_obj.base_dir))
        self.entry_base_dir = ctk.CTkEntry(
            self.header_frame, textvariable=self.base_dir_var, height=35
        )
        self.entry_base_dir.grid(row=0, column=1, sticky="ew", padx=10)

        self.btn_browse = ctk.CTkButton(
            self.header_frame,
            text="Elegir...",
            command=self.choose_base_dir,
            width=100,
            height=35,
        )
        self.btn_browse.grid(row=0, column=2, padx=15)

        # Boton ir a Reprocesar
        self.btn_goto_reprocess = ctk.CTkButton(
            self.header_frame,
            text="Ir a Reprocesar JSON",
            command=lambda: self.controller.show_frame("ReprocessScreen"),
            fg_color="#8e44ad",
            hover_color="#732d91",
            width=150,
            height=35
        )
        self.btn_goto_reprocess.grid(row=0, column=3, padx=15)

        # 2. Panel Central (Botones + Fechas)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(1, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)

        # 2.1 Columna Izquierda: Acciones
        self.actions_frame = ctk.CTkFrame(self.center_frame, corner_radius=10)
        self.actions_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.actions_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.actions_frame, text="Acciones", font=("Roboto Medium", 16)
        ).pack(pady=(15, 10))

        # Botones de acción con estilo
        btn_params = {"height": 40, "font": ("Roboto", 13), "corner_radius": 8}

        self.btn_scan = ctk.CTkButton(
            self.actions_frame,
            text="1) Escanear Pedidos (Dry-run)",
            command=self.on_scan_click,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            **btn_params
        )
        self.btn_scan.pack(fill="x", padx=20, pady=10)

        self.btn_process = ctk.CTkButton(
            self.actions_frame,
            text="2) Procesar Detalles",
            command=self.on_process_click,
            fg_color="#3498db",
            hover_color="#2980b9",
            **btn_params
        )
        self.btn_process.pack(fill="x", padx=20, pady=10)

        self.btn_accept = ctk.CTkButton(
            self.actions_frame,
            text="3) Aceptar y Descargar Guías",
            command=self.on_accept_click,
            fg_color="#e67e22",
            hover_color="#d35400",
            **btn_params
        )
        self.btn_accept.pack(fill="x", padx=20, pady=10)

        # Combo 2+3
        self.btn_auto_2_3 = ctk.CTkButton(
            self.actions_frame,
            text="2+3) Auto Procesar y Aceptar",
            command=self.on_auto_process_accept_click,
            fg_color="#D35400",
            hover_color="#A04000",
            **btn_params
        )
        self.btn_auto_2_3.pack(fill="x", padx=20, pady=10)

        self.btn_merge = ctk.CTkButton(
            self.actions_frame,
            text="4) Unir Guías PDF",
            command=self.on_merge_click,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            **btn_params
        )
        self.btn_merge.pack(fill="x", padx=20, pady=10)

        # Separador visual
        ctk.CTkFrame(self.actions_frame, height=2, fg_color="gray").pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.actions_frame, text="Antiguos (hace 5 días)", font=("Roboto Medium", 14)).pack(pady=(0, 5))

        self.btn_scan_old = ctk.CTkButton(
            self.actions_frame,
            text="5) Escanear Antiguos",
            command=self.on_scan_old_click,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            **btn_params
        )
        self.btn_scan_old.pack(fill="x", padx=20, pady=5)

        self.btn_process_old = ctk.CTkButton(
            self.actions_frame,
            text="6) Procesar Antiguos",
            command=self.on_process_old_click,
            fg_color="#6c7a89",
            hover_color="#bdc3c7",
            **btn_params
        )
        self.btn_process_old.pack(fill="x", padx=20, pady=5)

        # Registrar todos los botones de acción (para deshabilitar/habilitar)
        self._action_buttons = [
            self.btn_scan,
            self.btn_process,
            self.btn_accept,
            self.btn_auto_2_3,
            self.btn_merge,
            self.btn_scan_old,
            self.btn_process_old,
        ]

        # 2.2 Columna Derecha: Fechas
        self.dates_container = ctk.CTkFrame(self.center_frame, corner_radius=10)
        self.dates_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.dates_container.grid_rowconfigure(1, weight=1)
        self.dates_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.dates_container,
            text="Fechas con Pendientes",
            font=("Roboto Medium", 16),
        ).grid(row=0, column=0, pady=(15, 10))

        # Scrollable Frame para las fechas
        self.dates_scroll_frame = ctk.CTkScrollableFrame(
            self.dates_container, label_text="Selecciona fechas"
        )
        self.dates_scroll_frame.grid(
            row=1, column=0, sticky="nsew", padx=15, pady=(0, 15)
        )

        # 3. Log (Abajo)
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.log_frame, text="Registro de Actividad", font=("Roboto Medium", 14)
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(self.log_frame, height=150, font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # 4. Footer / Créditos
        self.footer_label = ctk.CTkLabel(
            self,
            text="Desarrollado por Jose Emmanuel Quintana Torres",
            font=("Roboto", 10),
            text_color="gray",
        )
        self.footer_label.grid(row=3, column=0, pady=(0, 10))

    # ------------------------------------------------------------------
    # Helpers: estado de botones y threading
    # ------------------------------------------------------------------

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self._action_buttons:
            btn.configure(state=state)

    def _run_action(self, action_fn, *args, post_ui=None):
        """
        Deshabilita los botones, lanza 'action_fn(*args)' en un hilo
        y re-habilita los botones cuando termina.
        'post_ui' es un callable opcional que se ejecuta en el hilo principal al terminar.
        """
        self._set_buttons_enabled(False)

        def _finish():
            self._set_buttons_enabled(True)
            if post_ui:
                post_ui()

        self.controller.run_in_thread(action_fn, *args, on_finish=_finish)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def choose_base_dir(self):
        folder = filedialog.askdirectory(
            title="Selecciona carpeta base",
            initialdir=str(self.controller.config_obj.base_dir),
        )
        if folder:
            self.base_dir_var.set(folder)
            self.controller.config_obj.base_dir = Path(folder)
            show_info(self, "Carpeta actualizada", f"Carpeta base cambiada a:\n{folder}")

    def append_log_screen(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def refresh_dates_checkboxes(self):
        # Limpiar widgets anteriores en el scroll frame
        for widget in self.dates_scroll_frame.winfo_children():
            widget.destroy()
        self.selected_dates_vars.clear()

        dates_summary = self.vm.get_dates_summary()
        if not dates_summary:
            ctk.CTkLabel(
                self.dates_scroll_frame,
                text="(No hay fechas con pendientes)",
                text_color="gray",
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

    def _get_selected_dates(self) -> list:
        return [d for d, var in self.selected_dates_vars.items() if var.get()]

    # ------------------------------------------------------------------
    # Handlers de botones (con threading)
    # ------------------------------------------------------------------

    def on_scan_click(self):
        self.controller.append_log("=== Iniciando escaneo ===")

        def _do():
            self.vm.scan_orders()

        def _after():
            self.controller.after(0, self.refresh_dates_checkboxes)
            self.controller.append_log("=== Escaneo terminado ===")
            self.controller.after(
                0,
                lambda: show_success(
                    self,
                    "Escaneo completado",
                    "Lista de pedidos guardada automáticamente en 'orders_auto_save.json'."
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
            self.controller.after(
                0,
                lambda: show_success(self, "Fase 1 completada", "Detalles procesados correctamente.\nRevisa las carpetas por día.")
            )

        self._run_action(_do, post_ui=_after)

    def on_accept_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para aceptar/descargar guías.")
            return

        self.controller.append_log(
            f"=== Fase 2: Aceptar + descargar guías para fechas: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.vm.accept_and_download_labels(selected_dates)

        def _after():
            self.controller.append_log("=== Proceso Fase 2 completado ===")
            self.controller.after(
                0,
                lambda: show_success(
                    self,
                    "Fase 2 completada",
                    "Pedidos aceptados y guías descargadas.\nRevisa la carpeta de cada día (subcarpeta 'guias' y GUIAS_<fecha>.pdf).",
                )
            )

        self._run_action(_do, post_ui=_after)

    def on_auto_process_accept_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para el proceso automático (2+3).")
            return

        self.controller.append_log(
            f"=== Iniciando PROCESO AUTOMÁTICO (2 y then 3) para: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.controller.append_log("--- [Auto] Paso 1: Procesar Detalles (Fase 1) ---")
            self.vm.process_details_dry_run(selected_dates)
            self.controller.append_log("--- [Auto] Paso 2: Aceptar y Descargar (Fase 2) ---")
            self.vm.accept_and_download_labels(selected_dates)

        def _after():
            self.controller.append_log("=== PROCESO AUTOMÁTICO COMPLETADO EXITOSAMENTE ===")
            self.controller.after(
                0,
                lambda: show_success(self, "Proceso automático completado", "Fases 2 y 3 ejecutadas correctamente.")
            )

        self._run_action(_do, post_ui=_after)

    def on_merge_click(self):
        selected_dates = self._get_selected_dates()
        if not selected_dates:
            show_warning(self, "Sin fechas", "Selecciona al menos una fecha para unir guías.")
            return

        self.controller.append_log(
            f"=== Fase 3: Uniendo guías para fechas: {', '.join(selected_dates)} ==="
        )

        def _do():
            self.vm.merge_labels(selected_dates)

        def _after():
            self.controller.append_log("=== Fase 3 completada ===")
            self.controller.after(
                0,
                lambda: show_success(
                    self,
                    "Guías unidas",
                    "PDF unificado generado correctamente.\nRevisa GUIAS_<fecha>.pdf en la carpeta del día.",
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
                0,
                lambda: show_success(self, "Escaneo completado", f"Pedidos antiguos encontrados para el rango:\n{date_str}")
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
            self.controller.after(
                0,
                lambda: show_success(
                    self,
                    "Proceso de antiguos completado",
                    "Screenshots y guías procesadas.\nRevisa las carpetas correspondientes."
                )
            )

        self._run_action(_do, post_ui=_after)


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
        self.grid_rowconfigure(2, weight=1)  # Log area expands

        # Header
        self.header = ctk.CTkFrame(self, corner_radius=10)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(self.header, text="Reprocesar Lista Guardada (Sin Validar Estado)", font=("Roboto Medium", 18))\
            .pack(pady=10)

        # Botones de Carga y Accion
        self.btns_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.btns_frame.pack(fill="x", padx=20, pady=10)

        self.btn_load = ctk.CTkButton(
            self.btns_frame,
            text="Cargar JSON",
            command=self.on_load_json,
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        self.btn_load.pack(side="left", padx=10)

        self.btn_run_reprocess = ctk.CTkButton(
            self.btns_frame,
            text="Ejecutar Reproceso",
            command=self.on_run_reprocess,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.btn_run_reprocess.pack(side="left", padx=10)

        self.btn_back = ctk.CTkButton(
            self.btns_frame,
            text="Volver",
            command=lambda: self.controller.show_frame("MainScreen"),
            fg_color="gray"
        )
        self.btn_back.pack(side="right", padx=10)

        self._action_buttons = [self.btn_load, self.btn_run_reprocess]

        # Area central: Lista de fechas cargadas
        self.mid_frame = ctk.CTkFrame(self)
        self.mid_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.mid_frame.grid_rowconfigure(1, weight=1)
        self.mid_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.mid_frame, text="Fechas en archivo cargado:", font=("Roboto Medium", 14))\
            .grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.dates_scroll = ctk.CTkScrollableFrame(self.mid_frame, height=200)
        self.dates_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Log Area
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12))
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self._action_buttons:
            btn.configure(state=state)

    def append_log_screen(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

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

        def _do():
            self.vm.reprocess_orders_json(selected)

        def _finish():
            self._set_buttons_enabled(True)
            self.controller.append_log("Reproceso completado.")
            self.controller.after(
                0,
                lambda: show_success(self, "Reproceso completado", "Los pedidos han sido reprocesados exitosamente.")
            )

        self.controller.run_in_thread(_do, on_finish=_finish)
