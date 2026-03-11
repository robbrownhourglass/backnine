"""Flask dashboard wrapper for Mountrath tee monitor."""

import config
from backnine_shared.dashboard import create_app


app = create_app(config)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.DASHBOARD_PORT, debug=False)
