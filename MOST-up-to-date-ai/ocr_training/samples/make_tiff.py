from pdf2image import convert_from_path
import os

# ─── Adjust these two lines if your folder names differ ───
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PDF_REL_PATH = os.path.join("scanned_pdfs", "SOL Box27C", "Document1.pdf")
OUTPUT_TIFF  = "sample0.tiff"
DPI          = 300

PDF_PATH = os.path.join(PROJECT_ROOT, PDF_REL_PATH)

# Convert page 1 of the PDF to a TIFF at 300 DPI
pages = convert_from_path(PDF_PATH, dpi=DPI)
pages[0].save(OUTPUT_TIFF, "TIFF")

print(f"Wrote {OUTPUT_TIFF} from {PDF_PATH}")

# this better work now 