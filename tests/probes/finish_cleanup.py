"""Close any open documents and leave the Documents tab showing the last order."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.screens import documents
from src.ui.driver import get_app, send_keys_to


def main():
    app = get_app()
    send_keys_to(app, "{ESC}")
    time.sleep(0.3)
    documents.close_all_tabs(app)
    documents.open_documents(app)
    print("tabs:", [t.window_text() for t in
                    app.wrapper.descendants(control_type="TabItem")])


main()
