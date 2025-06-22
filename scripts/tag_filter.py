
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
