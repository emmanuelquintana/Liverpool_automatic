from pathlib import Path

LIVERPOOL_ORDERS_URL = "https://marketplace.liverpool.com.mx/orders"

DEFAULT_BASE_DIR = Path(r"C:\Liverpool\auto")

# AHORA: carpeta exclusiva para el perfil del bot
DEFAULT_EDGE_USER_DATA_DIR = Path(r"C:\EdgeProfiles\LiverpoolAuto")

# Ya no usaremos profile_name, lo dejamos vacío o da igual
DEFAULT_EDGE_PROFILE_NAME = ""
PENDING_TEXT = "Pendiente de aceptación"
TIMEOUT = 120  # súbelo un poco para que te dé tiempo de poner el código de 2FA

DEFAULT_TIMEOUT = 120
DEFAULT_FALLBACK_DRIVER = r"C:\WebDrivers\msedgedriver.exe"
