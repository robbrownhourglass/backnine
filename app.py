from pathlib import Path

from backnine_shared.dashboard import create_multi_club_app


ROOT_DIR = Path(__file__).resolve().parent
app = create_multi_club_app(str(ROOT_DIR))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5080, debug=False)
