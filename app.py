"""Entry point. Run with: python app.py"""

import os

from hotroom import create_app

app = create_app()


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5050"))
    app.run(host=host, port=port, debug=False, use_reloader=False)
