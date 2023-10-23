""" This Class creates a window with a grid object that takes a data frame from pandas as input.
    It auto-sizes the rows and columns to display the data properly.  For your dataset, you may want to update the
    default size of the window.
    The update_dataframe method takes in a new data frame and updates the grid on the page.

    How to use:
        initial creation:
            self.gridDisplayWindow = GridPage("Put Your Title Here", width = 800, height = 200)
            self.gridDisplayWindow.update_dataframe(pandas_dataframe)
            self.gridDisplayWindow.Show()
        update without closing window:
            self.gridDisplayWindow.update_dataframe(updated_dataframe)

    **Important** Closing it when it's a child:
        If you use this as a child of a larger window, remember to create a custom "OnClose" for the parent window
        to ensure it gets destroyed when the parent is destroyed.
                def onClose(self, event):
                     if self.parent_window_name.gridDisplayWindow:
                        self.parent_window_name.gridDisplayWindow.Destroy()  # close the grid window
                    self.Destroy()

    That's it.

    note:
    The inspiration for this class came from here:
        https://www.blog.pythonlibrary.org/2010/04/04/wxpython-grid-tips-and-tricks/
    Although the capabilities are slightly different
    """

import wx
import wx.grid as gridlib
import itertools as it  # https://www.blog.pythonlibrary.org/2010/04/04/wxpython-grid-tips-and-tricks/


class GridPage(wx.Frame):

    def __init__(self, title, width, height):
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          title)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.grid = gridlib.Grid(self.panel)
        self.grid.CreateGrid(10, 10)
        self.width = width
        self.height = height
        self.grid.AutoSize()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND, 5)
        self.panel.SetSizer(sizer)

    def update_dataframe(self, input_dataframe):
        # if the grid has any columns and rows, delete them so we can start again
        if self.grid.NumberCols > 0 and self.grid.NumberRows > 0:
            self.grid.DeleteCols(0, self.grid.NumberCols, True)
            self.grid.DeleteRows(0, self.grid.NumberRows, True)

        # create a grid the size we need
        self.grid.AppendCols(input_dataframe.shape[1])
        self.grid.AppendRows(input_dataframe.shape[0])

        # set the column headers to be the values sent in from the dataframe
        for col in range(input_dataframe.shape[1]):
            self.grid.SetColLabelValue(col, input_dataframe.columns[col])

        # iterate over the grid setting the value and aligning the cell content.
        for row, col in it.product(range(len(input_dataframe)), range(len(input_dataframe.columns))):
            self.grid.SetCellValue(row, col, str(input_dataframe.iat[row, col]))  # set cell value
            self.grid.SetCellAlignment(row, col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)  # center vertically and horizontally

        # set the height and width of the cells such that all data is displayed, meaning columns and rows are expanded
        self.grid.AutoSize()
        self.SetSize(self.width, self.height)
        return


if __name__ == '__main__':
    import pandas as pd
    app = wx.App()
    df = pd.DataFrame({'test1': [2, 4, 8, 0],
                       'test2': [2, 0, 0, 0],
                       'special_test_3': [10, 2, 1, 8]})
    test = GridPage("My Window Title", width=800, height=200)
    test.update_dataframe(df)
    test.Show()
    app.MainLoop()
