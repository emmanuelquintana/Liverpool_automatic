# main.py
from models import AppConfig
from config import (
    DEFAULT_BASE_DIR,
    DEFAULT_EDGE_USER_DATA_DIR,
    DEFAULT_EDGE_PROFILE_NAME,
)
from view import LiverpoolApp


def main():
    config = AppConfig(
        base_dir=DEFAULT_BASE_DIR,
        edge_user_data_dir=DEFAULT_EDGE_USER_DATA_DIR,
        edge_profile_name=DEFAULT_EDGE_PROFILE_NAME,
    )

    app = LiverpoolApp(config)
    app.mainloop()


if __name__ == "__main__":
    main()
