from nbconvert import MarkdownExporter, PDFExporter
from traitlets.config import Config
import os
import nbformat
import json
import importlib.util
import textwrap

# Configuration for tagged cell filtering
c = Config()
c.TagFilterPreprocessor.enabled = True
c.TagFilterPreprocessor.remove_all_outputs = False   # Keep relevant outputs
c.TagFilterPreprocessor.remove_input = True         # Exclude code cells
c.TagRemovePreprocessor.remove_cell_tags = set()    # No tags to remove

# Custom preprocessor to filter tagged cells
tag_filter_path = os.path.join("scripts", "tag_filter.py")
with open(tag_filter_path, "w") as f:
    f.write(
        textwrap.dedent(
            r"""
            from nbconvert.preprocessors import Preprocessor

            class TagFilterPreprocessor(Preprocessor):
                def preprocess(self, nb, resources):
                    filtered_cells = []
                    for i, cell in enumerate(nb.cells):
                        tags = cell.metadata.get('tags', [])
                        if 'report' not in tags:  # Skip all cells unless tagged 'report'
                            continue
                        if cell.cell_type == 'code':
                            if 'keep_outputs' in tags:
                                cell.source = ""  # Remove code, keep only outputs (visualization)
                            elif 'keep_outputs' not in tags:
                                cell.outputs = []  # Clear outputs for code cells without 'keep_outputs'
                        filtered_cells.append(cell)
                    nb.cells = filtered_cells
                    print(f"Filtered cell indices: {[i for i in range(len(nb.cells))]}")  # Debug: Log filtered indices
                    return nb, resources
            """
        )
    )

# Dynamically load the preprocessor
spec = importlib.util.spec_from_file_location("tag_filter", tag_filter_path)
tag_filter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tag_filter_module)
TagFilterPreprocessor = tag_filter_module.TagFilterPreprocessor

# Register the preprocessor with the exporters
c.Exporter.preprocessors = [TagFilterPreprocessor]  # Explicitly register the custom preprocessor


# Load notebook to check structure
notebook_name = "notebooks/inspecting_data.ipynb"
if not os.path.exists(notebook_name):
    raise FileNotFoundError(f"Notebook {notebook_name} not found.")
with open(notebook_name, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

# Load config file and get ticker
config_path = "data/config.json"
if not os.path.exists(config_path):
    raise FileNotFoundError("Config file not found. Run fetch_data.py first.")
with open(config_path, 'r') as f:
    config = json.load(f)
stock_symbol = config["stock_symbol"].upper()

# Define output files
output_md_file = f"docs/findings_{stock_symbol.lower()}.md"
output_pdf_file = f"docs/findings_{stock_symbol.lower()}.pdf"


# Export markdown
try:
    markdown_exporter = MarkdownExporter(config=c)
    (markdown_body, resources) = markdown_exporter.from_filename(notebook_name)
    os.makedirs(os.path.dirname(output_md_file), exist_ok=True)
    with open(output_md_file, 'w', encoding='utf-8') as f:
        f.write(markdown_body)
    print(f"Markdown exported to {output_md_file}")
except Exception as e:
    print(f"Error exporting Markdown: {e}")

# Export PDF
try:
    pdf_exporter = PDFExporter(config=c)
    (pdf_body, resources) = pdf_exporter.from_filename(notebook_name)
    os.makedirs(os.path.dirname(output_pdf_file), exist_ok=True)
    with open(output_pdf_file, 'wb') as f:
        f.write(pdf_body)
    print(f"PDF exported to {output_pdf_file}")
except Exception as e:
    print(f"Error exporting PDF: {e}")
    # Fallback to webpdf if Latex fails
    os.system(f"jupyter nbconvert --to webpdf --TagFilterPreprocessor.enabled {notebook_name} --output={output_pdf_file}")
    print(f"Fallback PDF exported to {output_pdf_file}")