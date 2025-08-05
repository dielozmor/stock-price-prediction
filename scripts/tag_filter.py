#!/usr/bin/env python3
"""
A custom preprocessor for nbconvert that filters notebook cells, keeping only those tagged with 'export'.
"""

from nbconvert.preprocessors import Preprocessor

class TagFilterPreprocessor(Preprocessor):
    def preprocess(self, nb, resources):
        filtered_cells = []
        for cell in nb.cells:
            tags = cell.get('metadata', {}).get('tags', [])
            if "export" in tags:
                filtered_cells.append(cell)
        nb.cells = filtered_cells
        return nb, resources