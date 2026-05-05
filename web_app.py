# web_app.py
import os
import threading
import logging
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends, Cookie, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from pydantic import BaseModel

from models import AppConfig, DayBatch
from services import LiverpoolService
from settings import load_settings
from config import (
    DEFAULT_BASE_DIR,
    DEFAULT_EDGE_USER_DATA_DIR,
    DEFAULT_EDGE_PROFILE_NAME,
    DEFAULT_TIMEOUT,
    DEFAULT_FALLBACK_DRIVER,
)

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_app")

# --- Credenciales Web (Variables de Entorno) ---
WEB_USER = os.getenv("WEB_USER", "emmanuel")
WEB_PASS = os.getenv("WEB_PASS", "4mmA180516")
SESSION_ID = str(uuid.uuid4()) # Sesión simple para esta ejecución

# --- Estado Global de la App ---
class AppState:
    def __init__(self):
        self.service: Optional[LiverpoolService] = None
        self.days: Dict[str, DayBatch] = {}
        self.logs: List[Dict] = [] # Lista de diccionarios {id, time, msg}
        self.progress = {"current": 0, "total": 0, "label": ""}
        self.running = False
        self.error = None
        
        # Interactividad
        self.pending_input: Optional[Dict] = None # {label, placeholder, type}
        self.input_event = threading.Event()
        self.provided_value: Optional[str] = None
        
        self.last_update = datetime.now()

    def add_log(self, msg: str):
        log_id = len(self.logs)
        self.logs.append({
            "id": log_id,
            "time": datetime.now().strftime('%H:%M:%S'),
            "msg": msg
        })
        self.last_update = datetime.now()

    def update_progress(self, current: int, total: int, label: str):
        self.progress = {"current": current, "total": total, "label": label}
        self.last_update = datetime.now()

    def request_input(self, label: str, placeholder: str, input_type: str) -> str:
        """Callback para el servicio: pausa y espera entrada del usuario."""
        self.pending_input = {
            "label": label,
            "placeholder": placeholder,
            "type": input_type
        }
        self.add_log(f"[WAITING] Requerida intervención del usuario: {label}")
        self.input_event.clear()
        self.input_event.wait() # Pausa el hilo del bot
        
        res = self.provided_value
        self.pending_input = None
        self.provided_value = None
        return res or ""

state = AppState()

# --- Instancia FastAPI ---
app = FastAPI(title="Liverpool Automatic Web")

# Servir archivos estáticos (frontend)
current_dir = Path(__file__).resolve().parent
web_dir = current_dir / "web"
web_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

templates = Jinja2Templates(directory=str(web_dir))

# --- Seguridad (Auth Simple) ---
def get_current_user(session_token: Optional[str] = Cookie(None)):
    if session_token != SESSION_ID:
        raise HTTPException(status_code=401, detail="No autorizado")
    return WEB_USER

# --- Modelos de Datos para API ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ScanRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ProcessRequest(BaseModel):
    dates: List[str]

class InputResponse(BaseModel):
    value: str

# --- Auxiliares ---
def get_service_instance():
    saved = load_settings()
    # Usar headless si estamos en Docker (detectado por ENV)
    is_docker = os.path.exists('/.dockerenv') or os.getenv("DOCKER_MODE") == "true"
    
    config = AppConfig(
        base_dir=Path(saved.get("base_dir", str(DEFAULT_BASE_DIR))),
        edge_user_data_dir=DEFAULT_EDGE_USER_DATA_DIR if not is_docker else None,
        edge_profile_name=DEFAULT_EDGE_PROFILE_NAME,
        timeout=int(saved.get("timeout", DEFAULT_TIMEOUT)),
        fallback_driver=saved.get("fallback_driver", DEFAULT_FALLBACK_DRIVER),
        overwrite_outputs=bool(saved.get("overwrite_outputs", True)),
        headless=is_docker,
        download_dir=None
    )
    
    svc = LiverpoolService(
        config=config,
        log_callback=state.add_log,
        progress_callback=state.update_progress,
        input_callback=state.request_input
    )
    return svc

# --- Endpoints Auth ---

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/api/v1/login")
async def login_api(data: LoginRequest, response: Response):
    if data.username == WEB_USER and data.password == WEB_PASS:
        response.set_cookie(key="session_token", value=SESSION_ID, httponly=True)
        return {"message": "OK"}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie("session_token")
    return RedirectResponse(url="/login")

# --- Endpoints Protegidos ---

@app.get("/")
async def read_root(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token != SESSION_ID:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.get("/api/v1/status")
async def get_status(user: str = Depends(get_current_user)):
    return {
        "running": state.running,
        "progress": state.progress,
        "logs": state.logs[-100:], 
        "days": {date: batch.to_dict() for date, batch in state.days.items()},
        "error": state.error,
        "pending_input": state.pending_input
    }

@app.post("/api/v1/provide-input")
async def provide_input(data: InputResponse, user: str = Depends(get_current_user)):
    state.provided_value = data.value
    state.input_event.set()
    return {"message": "Input recibido"}

@app.post("/api/v1/scan")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks, user: str = Depends(get_current_user)):
    if state.running:
        raise HTTPException(status_code=400, detail="Ya hay un proceso en curso")
    
    state.running = True
    state.logs = []
    state.error = None
    state.days = {}
    
    def run_scan():
        try:
            svc = get_service_instance()
            if request.start_date and request.end_date:
                state.days = svc.scan_orders_in_range(request.start_date, request.end_date)
            else:
                state.days = svc.scan_orders()
            state.add_log("Escaneo completado exitosamente.")
        except Exception as e:
            logger.exception("Error en escaneo")
            state.error = str(e)
            state.add_log(f"ERROR: {e}")
        finally:
            state.running = False

    background_tasks.add_task(run_scan)
    return {"message": "Escaneo iniciado"}

@app.post("/api/v1/process/phase1")
async def start_phase1(request: ProcessRequest, background_tasks: BackgroundTasks, user: str = Depends(get_current_user)):
    if state.running:
        raise HTTPException(status_code=400, detail="Ya hay un proceso en curso")
    
    if not request.dates:
        raise HTTPException(status_code=400, detail="No hay fechas seleccionadas")

    state.running = True
    state.error = None
    state.progress = {"current": 0, "total": 0, "label": "Iniciando Fase 1..."}

    def run_phase1():
        try:
            svc = get_service_instance()
            # Fase 1: Dry Run (Fotos + Excel)
            svc.process_details_dry_run(state.days, request.dates)
            state.add_log("Fase 1 (Previsualización) completada exitosamente.")
        except Exception as e:
            logger.exception("Error en Fase 1")
            state.error = str(e)
            state.add_log(f"ERROR: {e}")
        finally:
            state.running = False

    background_tasks.add_task(run_phase1)
    return {"message": "Fase 1 iniciada"}

@app.post("/api/v1/process/phase2")
async def start_phase2(request: ProcessRequest, background_tasks: BackgroundTasks, user: str = Depends(get_current_user)):
    if state.running:
        raise HTTPException(status_code=400, detail="Ya hay un proceso en curso")
    
    if not request.dates:
        raise HTTPException(status_code=400, detail="No hay fechas seleccionadas")

    state.running = True
    state.error = None
    state.progress = {"current": 0, "total": 0, "label": "Iniciando Fase 2..."}

    def run_phase2():
        try:
            svc = get_service_instance()
            # Fase 2: Aceptar + Descargar
            svc.accept_and_download_labels(state.days, request.dates)
            state.add_log("Fase 2 (Aceptar/Descargar) completada exitosamente.")
        except Exception as e:
            logger.exception("Error en Fase 2")
            state.error = str(e)
            state.add_log(f"ERROR: {e}")
        finally:
            state.running = False

    background_tasks.add_task(run_phase2)
    return {"message": "Fase 2 iniciada"}

@app.post("/api/v1/reprocess")
async def start_reprocess(request: ProcessRequest, background_tasks: BackgroundTasks, user: str = Depends(get_current_user)):
    if state.running:
        raise HTTPException(status_code=400, detail="Ya hay un proceso en curso")
    
    state.running = True
    state.error = None
    
    def run_reprocess():
        try:
            svc = get_service_instance()
            svc.reprocess_orders_execution(state.days, request.dates)
            state.add_log("Reprocesamiento finalizado.")
        except Exception as e:
            logger.exception("Error en reprocesar")
            state.error = str(e); state.add_log(f"ERROR: {e}")
        finally:
            state.running = False

    background_tasks.add_task(run_reprocess)
    return {"message": "Reproceso iniciado"}

@app.post("/api/v1/old_orders")
async def start_old_orders(request: ProcessRequest, background_tasks: BackgroundTasks, user: str = Depends(get_current_user)):
    if state.running:
        raise HTTPException(status_code=400, detail="Ya hay un proceso en curso")
    
    state.running = True
    state.error = None
    
    def run_old():
        try:
            svc = get_service_instance()
            svc.process_old_orders_execution(state.days, request.dates)
            state.add_log("Proceso de pedidos antiguos finalizado.")
        except Exception as e:
            logger.exception("Error en antiguos")
            state.error = str(e); state.add_log(f"ERROR: {e}")
        finally:
            state.running = False

    background_tasks.add_task(run_old)
    return {"message": "Proceso antiguos iniciado"}

@app.get("/api/v1/download/{date}/{filename}")
async def download_file(date: str, filename: str, user: str = Depends(get_current_user)):
    saved = load_settings()
    base_dir = Path(saved.get("base_dir", str(DEFAULT_BASE_DIR)))
    file_path = (base_dir / date / filename).resolve()
    
    if not file_path.exists():
        file_path = (base_dir / date / "guias" / filename).resolve()
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {filename}")
    
    return FileResponse(path=file_path, filename=filename)

# --- Ejecución ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
