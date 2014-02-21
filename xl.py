from functools import partial
import xlrd

def _get_sheet(self, index_or_name):
    if isinstance(index_or_name, (int, long)):
        return self.sheet_by_index(index_or_name)
    return self.sheet_by_name(index_or_name)
xlrd.book.Book.__getitem__ = _get_sheet
del _get_sheet

def _get_cell(self, row_col, only_col=None):
    if only_col is None:
        row, col = row_col
    else:
        row, col = row_col, only_col
    return self.cell(row, col)
xlrd.sheet.Sheet.__getitem__ = _get_cell
del _get_cell

def _rows_gen(self, start_row=0, end_row=None, start_col=0, end_col=None):
    "returns each row as a list of values"
    if end_row is None:
        end_row = self.nrows
    for y in xrange(start_row, end_row):
        yield self.row_values(y, start_col, end_col)
xlrd.sheet.Sheet.rows = _rows_gen
del _rows_gen

open_workbook = partial(xlrd.open_workbook, on_demand=True)
