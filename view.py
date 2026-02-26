# view.py
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path

from models import AppConfig
from viewmodel import LiverpoolViewModel

# Configuración global de CustomTkinter
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class LiverpoolApp(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.title("Liverpool Orders - Fase 1 (Dry-run)")
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
        # Envia log a todas las pantallas que tengan metodo log
        for frame in self.frames.values():
            if hasattr(frame, "append_log_screen"):
                frame.append_log_screen(msg)

class MainScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.vm = controller.vm
        self.selected_dates_vars = {}
        
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
            fg_color="#D35400",  # Un color distinto, mezcla de azul y naranja
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

    def choose_base_dir(self):
        folder = filedialog.askdirectory(
            title="Selecciona carpeta base",
            initialdir=str(self.controller.config_obj.base_dir),
        )
        if folder:
            self.base_dir_var.set(folder)
            self.controller.config_obj.base_dir = Path(folder)

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

    def on_scan_click(self):
        try:
            self.controller.append_log("=== Iniciando escaneo ===")
            self.vm.scan_orders()
            self.refresh_dates_checkboxes()
            self.controller.append_log("=== Escaneo terminado ===")
            messagebox.showinfo("Autoguardado", "Se ha guardado la lista de pedidos en 'orders_auto_save.json'")
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el escaneo: {e}")

    def on_process_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para procesar."
            )
            return

        self.controller.append_log(
            f"=== Procesando detalles (dry-run) para fechas: {', '.join(selected_dates)} ==="
        )
        try:
            self.vm.process_details_dry_run(selected_dates)
            self.controller.append_log("=== Proceso Fase 1 completado ===")
            messagebox.showinfo(
                "Listo", "Fase 1 completada. Revisa las carpetas por día."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando detalles: {e}")

    def on_accept_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para aceptar/descargar guías."
            )
            return

        self.controller.append_log(
            f"=== Fase 2: Aceptar + descargar guías para fechas: {', '.join(selected_dates)} ==="
        )
        try:
            self.vm.accept_and_download_labels(selected_dates)
            self.controller.append_log("=== Proceso Fase 2 completado ===")
            messagebox.showinfo(
                "Listo",
                "Fase 2 completada. Revisa la carpeta de cada día (subcarpeta 'guias' y GUIAS_<fecha>.pdf).",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error en Fase 2: {e}")

    def on_auto_process_accept_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para el proceso automático (2+3)."
            )
            return

        self.controller.append_log(
            f"=== Iniciando PROCESO AUTOMÁTICO (2 y then 3) para: {', '.join(selected_dates)} ==="
        )

        try:
            self.controller.append_log("--- [Auto] Paso 1: Procesar Detalles (Fase 1) ---")
            self.vm.process_details_dry_run(selected_dates)
        except Exception as e:
            messagebox.showerror("Error Auto", f"Falló Fase 1 en automático: {e}")
            self.controller.append_log(f"!!! Error en Fase 1: {e}")
            return

        try:
            self.controller.append_log("--- [Auto] Paso 2: Aceptar y Descargar (Fase 2) ---")
            self.vm.accept_and_download_labels(selected_dates)
            
            self.controller.append_log("=== PROCESO AUTOMÁTICO COMPLETADO EXITOSAMENTE ===")
            messagebox.showinfo(
                "Listo",
                "Proceso Automático (2+3) completado."
            )
        except Exception as e:
            messagebox.showerror("Error Auto", f"Falló Fase 2 en automático: {e}")
            self.controller.append_log(f"!!! Error en Fase 2: {e}")

    def on_merge_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para unir guías."
            )
            return

        self.controller.append_log(
            f"=== Fase 3: Uniendo guías para fechas: {', '.join(selected_dates)} ==="
        )
        try:
            self.vm.merge_labels(selected_dates)
            self.controller.append_log("=== Fase 3 completada ===")
            messagebox.showinfo(
                "Listo",
                "Fase 3 completada. Revisa los PDF GUIAS_<fecha>.pdf y los TXT de faltantes.",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error uniendo guías: {e}")

    def on_scan_old_click(self):
        try:
            self.controller.append_log("=== Escaneando pedidos antiguos (5 días antes) ===")
            date_str = self.vm.scan_old_orders_5_days_ago()
            self.refresh_dates_checkboxes()
            self.controller.append_log(f"=== Escaneo de antiguos ({date_str}) finalizado ===")
        except Exception as e:
            messagebox.showerror("Error", f"Error escaneando antiguos: {e}")
            self.controller.append_log(f"!!! Error escaneando antiguos: {e}")

    def on_process_old_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para procesar antiguos."
            )
            return

        self.controller.append_log(f"=== Procesando Antiguos para: {', '.join(selected_dates)} ===")
        try:
            self.vm.process_old_orders_execution(selected_dates)
            self.controller.append_log("=== Proceso de Antiguos completado ===")
            messagebox.showinfo(
                "Listo", 
                "Proceso de antiguos completado.\n"
                "Revisa las carpetas correspondientes."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando antiguos: {e}")
            self.controller.append_log(f"!!! Error procesando antiguos: {e}")

class ReprocessScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.vm = controller.vm
        self.selected_dates_vars = {}
        
        self._build_ui()
        
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Log area expands

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
            messagebox.showinfo("Carga Exitosa", "Se han cargado los pedidos del archivo JSON.")
        except Exception as e:
            messagebox.showerror("Error Carga", f"No se pudo cargar el archivo: {e}")

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
            messagebox.showwarning("Atención", "Selecciona fechas para reprocesar.")
            return
            
        self.controller.append_log(f"Iniciando REPROCESO para: {len(selected)} fechas.")
        try:
            self.vm.reprocess_orders_json(selected)
            self.controller.append_log("Reproceso completado.")
            messagebox.showinfo("Fin", "Reproceso completado.")
        except Exception as e:
            messagebox.showerror("Error", f"Error en reproceso: {e}")
            self.controller.append_log(f"Error: {e}")
