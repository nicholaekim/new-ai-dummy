from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PDFHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if event.src_path.lower().endswith(".pdf"):
            self.callback(event.src_path)

def start_watcher(callback, directories: list[str]):
    """Monitor given directories for new PDFs and call callback(path)."""
    observer = Observer()
    handler = PDFHandler(callback)
    for d in directories:
        observer.schedule(handler, d, recursive=False)
    observer.start()
    observer.join()
