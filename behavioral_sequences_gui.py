import os
import wx
import threading
import pandas as pd
from pathlib import Path
import platform, subprocess
from GridPage import GridPage
import behavioral_sequences_backend


# Class: DynamicBackgroundInitialWindow
# Description: This class was taken from LabGym and then modified for User input
class BehaviorSequencesInitialWindow(wx.Frame):

    def __init__(self, title, mode='MIN'):
        wx.Frame.__init__(self, parent=None, title=title)
        self.panel = ControlPanel(self, mode=mode)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.frame_sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(self.frame_sizer)
        self.Size = (self.panel.BestVirtualSize[0] + 30, self.panel.BestVirtualSize[1] + 40)
        self.Move(wx.Point(50, 50))
        self.Show()

    # Make a custom close event to ensure the results window is closed whenever the main window closes
    def onClose(self, event):
        if self.panel.results:
            self.panel.results.Destroy()  # close the results window
        self.Destroy()  # close the main window


class ControlPanel(wx.ScrolledWindow):

    def __init__(self, parent, mode='TEST'):
        wx.ScrolledWindow.__init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize,
                                   style=wx.HSCROLL | wx.VSCROLL,
                                   name="scrolledWindow")
        self.filtered_dataframe = None
        self.min_duration = 0
        self.results = None
        self.min_mean_confidence = 0
        self.min_depth = 2
        self.max_depth = 2
        self.behavior_filter = []
        self.behavior_list = []
        self.SetScrollbars(1, 1, 600, 400)

        # Set up the variables that we want to capture
        self.inference_size = None
        self.animals = None
        self.dataframe = None
        self.thing_choice = None
        self.model_path = None
        self.model_folder_path = None
        self.thing_names_path = None
        self.video_path = None
        self.detection_threshold = None
        self.output_path = os.path.join(os.getcwd(), 'videos_output')
        self.input_path = None
        self.display_things = []
        self.percent_video_complete = 0
        self.mode = mode

        # Get the user's input Excel file
        get_input_button = wx.Button(self, label='Select An Excel File to Analyze')
        get_input_button.Bind(wx.EVT_BUTTON, self.evt_get_input)
        self.get_input_label = wx.TextCtrl(self, value='{your input}', style=wx.TE_LEFT, size=(300, -1))

        # Get the length of sequences they want to capture
        self.sequence_length_text = wx.StaticText(self, label='Sequence Length')
        self.sequence_length_widget = wx.SpinCtrl(self, min=1, max=3, initial=2)
        self.sequence_length_widget.Bind(wx.EVT_SPINCTRLDOUBLE, self.evt_set_sequence_length)
        self.sequence_length = self.sequence_length_widget.GetValue()
        self.sequence_length_text.Disable()
        self.sequence_length_widget.Hide()
        self.sequence_length_text.Hide()
        # self.sequence_length.Disable()

        # Process those sequences
        self.process_sequences_button = wx.Button(self, label='Process Sequences')
        self.process_sequences_button.Bind(wx.EVT_BUTTON, self.evt_process_sequences)

        # Filters (confidence and duration)
        self.min_duration_text = wx.StaticText(self, label='Minimum \nDuration (s)',
                                               style=wx.ALIGN_CENTER_HORIZONTAL)
        self.min_duration_widget = wx.SpinCtrlDouble(self, initial=0.0, min=0.0, max=9999.0, inc=0.005)
        self.min_duration_text.SetToolTip('Enter the minimum total duration for a valid behavior sequence')
        self.min_duration_widget.SetToolTip('Enter the minimum total duration for a valid behavior sequence')
        self.min_duration_widget.Bind(wx.EVT_SPINCTRLDOUBLE, self.evt_set_filter)
        self.min_mean_confidence_text = wx.StaticText(self, label='Minimum \nConfidence (mean)',
                                                      style=wx.ALIGN_CENTER_HORIZONTAL)
        self.min_mean_confidence_text.SetToolTip('Confidence that the sequence was accurately identified. '
                                                 '(Mean across all samples)')
        self.min_mean_confidence_widget = wx.SpinCtrlDouble(self, initial=0.0, min=0.0, max=1.0, inc=0.05)
        self.min_mean_confidence_widget.Bind(wx.EVT_SPINCTRLDOUBLE, self.evt_set_filter)
        self.min_mean_confidence_widget.SetToolTip('Confidence that the sequence was accurately identified. '
                                                   '(Mean across all samples)')

        self.min_depth_text = wx.StaticText(self, label='Minimum \nSequence Depth',
                                                      style=wx.ALIGN_CENTER_HORIZONTAL)
        self.min_depth_text.SetToolTip('Minimum number of behaviors in a sequence to detect')
        self.min_depth_widget = wx.SpinCtrl(self, initial=2, min=2, max=999)
        self.min_depth_widget.Bind(wx.EVT_SPINCTRL, self.evt_set_filter)
        self.min_depth_widget.SetToolTip('Minimum number of behaviors in a sequence to detect')

        self.max_depth_text = wx.StaticText(self, label='Maximum \nSequence Depth',
                                            style=wx.ALIGN_CENTER_HORIZONTAL)
        self.max_depth_text.SetToolTip('Maximum number of behaviors in a sequence to detect')
        self.max_depth_widget = wx.SpinCtrl(self, initial=2, min=2, max=999)
        self.max_depth_widget.Bind(wx.EVT_SPINCTRL, self.evt_set_filter)
        self.max_depth_widget.SetToolTip('Maximum number of behaviors in a sequence to detect')

        self.clear_filter_default_button = wx.Button(self, label='Clear Filter')
        self.clear_filter_default_button.SetToolTip('Clear Sequence Filter')
        self.clear_filter_default_button.Bind(wx.EVT_BUTTON, self.evt_clear_filter_default)

        self.set_behavior_filter_button = wx.Button(self, label='Customize Filter')
        self.set_behavior_filter_button.SetToolTip('Select Sequences to Include in Results \n'
                                                   'If none are selected, the filter is deactivated')
        self.set_behavior_filter_button.Bind(wx.EVT_BUTTON, self.evt_set_behavior_filter)

        # Done button and closing everything
        save_button = wx.Button(self, label='Save')
        save_button.Bind(wx.EVT_BUTTON, self.evt_save_results)

        view_results_file_button = wx.Button(self, label='View Results File')
        view_results_file_button.Bind(wx.EVT_BUTTON, self.evt_open_result_file)

        show_results_button = wx.Button(self, label='Show Results')
        show_results_button.Bind(wx.EVT_BUTTON, self.evt_show_results)

        # Set up the container (BoxSizer) for the overall display window. Within this window, we will
        # place additional containers for sets of input and capabilities.
        overall_window_vertical = wx.BoxSizer(wx.VERTICAL)
        overall_window_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        overall_window_vertical.Add(0, 15)

        # Add input to the top of the container
        get_input_sizer_vertical = wx.StaticBox(self)
        get_input_options_vertical = wx.StaticBoxSizer(get_input_sizer_vertical, wx.VERTICAL)
        get_input_options = wx.BoxSizer(wx.HORIZONTAL)

        get_input_options.Add(get_input_button)
        get_input_options.Add(10, 0)
        get_input_options.Add(self.get_input_label, wx.EXPAND)
        get_input_options_vertical.Add(0, 5)
        get_input_options_vertical.Add(get_input_options, wx.ALIGN_CENTER_VERTICAL, wx.EXPAND)

        # Add the model options to the vertical window container
        overall_window_vertical.Add(get_input_options_vertical, flag=wx.EXPAND)

        overall_window_vertical.Add(0, 5)
        # Place the "Process image" button
        process_sequence_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        process_sequence_button_sizer.Add(10, 0)
        process_sequence_button_sizer.Add(self.process_sequences_button, wx.LEFT)

        # Add the image options to the vertical window container
        overall_window_vertical.Add(process_sequence_button_sizer)

        #
        # Create the individual boxes to hold filtering buttons
        #
        min_duration_box = wx.StaticBox(self)
        min_duration_sizer = wx.StaticBoxSizer(min_duration_box, wx.VERTICAL)
        min_duration_sizer.Add(self.min_duration_text, flag=wx.ALIGN_CENTER_HORIZONTAL)
        min_duration_sizer.Add(self.min_duration_widget, flag=wx.ALIGN_CENTER_HORIZONTAL)
        min_mean_confidence_box = wx.StaticBox(self)
        min_mean_confidence_sizer = wx.StaticBoxSizer(min_mean_confidence_box, wx.VERTICAL)
        min_mean_confidence_sizer.Add(self.min_mean_confidence_text, flag=wx.ALIGN_CENTER_HORIZONTAL)
        min_mean_confidence_sizer.Add(self.min_mean_confidence_widget, flag=wx.ALIGN_CENTER_HORIZONTAL)

        min_depth_box = wx.StaticBox(self)
        min_depth_sizer = wx.StaticBoxSizer(min_depth_box, wx.VERTICAL)
        min_depth_sizer.Add(self.min_depth_text, flag=wx.ALIGN_CENTER_HORIZONTAL)
        min_depth_sizer.Add(self.min_depth_widget, flag=wx.ALIGN_CENTER_HORIZONTAL)
        max_depth_box = wx.StaticBox(self)
        max_depth_sizer = wx.StaticBoxSizer(max_depth_box, wx.VERTICAL)
        max_depth_sizer.Add(self.max_depth_text, flag=wx.ALIGN_CENTER_HORIZONTAL)
        max_depth_sizer.Add(self.max_depth_widget, flag=wx.ALIGN_CENTER_HORIZONTAL)

        behavior_filter_box = wx.StaticBox(self)
        behavior_filter_sizer = wx.StaticBoxSizer(behavior_filter_box, wx.VERTICAL)
        behavior_filter_sizer.Add(self.clear_filter_default_button, flag=wx.ALIGN_CENTER_HORIZONTAL)
        behavior_filter_sizer.Add(0, 10)
        behavior_filter_sizer.Add(self.set_behavior_filter_button, flag=wx.ALIGN_CENTER_HORIZONTAL)

        #
        # Create the area to hold the individual filtering button boxes and add them
        #
        filter_behavior_sequences_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        filter_behavior_sequences_box = wx.StaticBox(self)
        filter_behavior_sequences_options_vertical_sizer = (
            wx.StaticBoxSizer(filter_behavior_sequences_box, wx.VERTICAL))
        filter_behavior_sequences_parts_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        filter_behavior_sequences_parts_horizontal.Add(5, 0)
        filter_behavior_sequences_parts_horizontal.Add(min_duration_sizer, flag=wx.ALIGN_CENTER_VERTICAL)
        filter_behavior_sequences_parts_horizontal.Add(5, 0)
        filter_behavior_sequences_parts_horizontal.Add(min_mean_confidence_sizer, flag=wx.ALIGN_CENTER_VERTICAL)
        filter_behavior_sequences_parts_horizontal.Add(5, 0)
        filter_behavior_sequences_parts_horizontal.Add(min_depth_sizer, flag=wx.ALIGN_CENTER_VERTICAL)
        filter_behavior_sequences_parts_horizontal.Add(5, 0)
        filter_behavior_sequences_parts_horizontal.Add(max_depth_sizer, flag=wx.ALIGN_CENTER_VERTICAL)
        filter_behavior_sequences_parts_horizontal.Add(10, 0)
        filter_behavior_sequences_parts_horizontal.Add(behavior_filter_sizer, wx.CENTER)
        filter_behavior_sequences_options_vertical_sizer.Add(filter_behavior_sequences_parts_horizontal, wx.LEFT)
        filter_behavior_sequences_horizontal.Add(filter_behavior_sequences_options_vertical_sizer,
                                                 wx.ALIGN_CENTER_HORIZONTAL)

        overall_window_vertical.Add(0, 5)
        overall_window_vertical.Add(filter_behavior_sequences_horizontal, flag=wx.EXPAND)

        ### Add to overall window
        save_button_horizontal = wx.BoxSizer(wx.HORIZONTAL)
        save_box = wx.StaticBox(self)
        save_sizer = wx.StaticBoxSizer(save_box, wx.VERTICAL)
        save_sizer.Add(show_results_button)
        save_sizer.Add(0, 10)
        save_sizer.Add(save_button)
        save_sizer.Add(0, 10)
        save_sizer.Add(view_results_file_button)
        save_button_horizontal.Add(save_sizer)
        overall_window_vertical.Add(save_button_horizontal, wx.LEFT)
        overall_window_vertical.Add(0, 5)
        overall_window_horizontal.Add(15, 0)
        overall_window_horizontal.Add(overall_window_vertical, wx.EXPAND)
        overall_window_horizontal.Add(15, 0)
        self.SetSizer(overall_window_horizontal)

    def cleanData(self, original_input):
        original_input = original_input.replace('[', '')
        original_input = original_input.replace(']', '')
        original_input = original_input.replace("'", '')
        original_input = original_input.replace(" ", '')
        clean_input = original_input.split(',')
        return clean_input

    def get_behavioral_sequences(self):
        # Make variables for later UI config
        # min_depth and max_depth which is number of behaviors in a row to consider
        file_name = self.input_path
        min_depth = self.min_depth
        max_depth = self.max_depth
        self.dataframe = behavioral_sequences_backend.process_file(self.input_path, min_depth, max_depth)
        self.behavior_list = list(self.dataframe['behavioral_sequence_name'].unique())
        self.behavior_list.sort()

    def evt_save_results(self, event):
        output_filename = f'{Path(self.input_path).stem}_sequences.xlsx'
        with wx.FileDialog(None, message='Save Results', defaultDir=self.output_path,
                           defaultFile=output_filename,
                           wildcard='Excel Files(*.xlsx)|*.xlsx',
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as saveFile:
            if saveFile.ShowModal() == wx.ID_CANCEL:
                return
            filename = saveFile.GetPath()
            self.output_path = os.path.dirname(filename)
            if self.filtered_dataframe is None:
                self.filtered_dataframe = self.dataframe
            self.filtered_dataframe.to_excel(filename, index=False)
        return

    def evt_open_result_file(self, event):
        with wx.FileDialog(None, message='Open Results File', defaultDir=self.output_path,
                           wildcard='Excel Files(*.xlsx)|*.xlsx',
                           style=wx.FD_OPEN) as openFile:
            if openFile.ShowModal() == wx.ID_CANCEL:
                return
            filename = openFile.GetPath()
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', filename))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(filename)
            else:  # linux variants
                subprocess.call(('xdg-open', filename))
        return

    def evt_done(self, event):
        self.Parent.Destroy()

    # Function: evt_get_input_directory
    # Description: basic modal directory dialog box to get the input directory
    def evt_set_sequence_length(self, event):
        self.sequence_length = self.sequence_length_widget.GetValue()

    # Function: evt_get_input_directory
    # Description: basic modal directory dialog box to get the input directory
    def evt_get_input(self, event):
        wildcard = "Excel Files (*.xlsx, *.xls)|*.xlsx;*.xls"
        dlg = wx.FileDialog(
            self, message="Choose an Excel File for Input",
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.input_path = path
            self.get_input_label.SetValue(os.path.basename(path))
        dlg.Destroy()

    # Function: evt_get_video_output_directory
    # Description: basic modal directory dialog box to get the output directory
    """ def evt_get_video_output_directory(self, event):
        dlg = wx.DirDialog(None, "Choose output directory", "",
                           wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.output_path = dlg.GetPath()
            self.get_video_output_directory_label.LabelText = ": " + self.output_path
        dlg.Destroy() """

    def evt_process_sequences(self, event):
        if not self.input_path:
            dlg = wx.GenericMessageDialog(None, 'No input file has been selected!', caption='Error',
                                          style=wx.OK | wx.CENTER)
            dlg.ShowModal()
            return
        if not self.sequence_length:
            dlg = wx.GenericMessageDialog(None, 'No sequence length has been selected!', caption='Error',
                                          style=wx.OK | wx.CENTER)
            dlg.ShowModal()
            return
        try:
            thread = threading.Thread(target=self.get_behavioral_sequences)
            thread.run()
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
            dlg = wx.GenericMessageDialog(None,
                                          "Invalid data in Input Behavior File. "
                                          "Select a different File",
                                          caption='Error',
                                          style=wx.OK | wx.CENTER)
            dlg.ShowModal()

    def evt_set_filter(self, event):
        self.min_duration = self.min_duration_widget.GetValue()
        self.min_mean_confidence = self.min_mean_confidence_widget.GetValue()
        self.min_depth = self.min_depth_widget.GetValue()
        self.max_depth = self.max_depth_widget.GetValue()

    def evt_set_behavior_filter(self, event):
        checked_items = []
        dlg = wx.MultiChoiceDialog(self, "Pick the behaviors you want included in the results (default is all)",
                                   "Pick Behaviors", self.behavior_list)
        if self.behavior_filter != self.behavior_list:
            for sequence in self.behavior_filter:
                checked_items.append(self.behavior_list.index(sequence))
        dlg.SetSelections(checked_items)
        if dlg.ShowModal() == wx.ID_OK:
            self.behavior_filter = []
            for selection in dlg.GetSelections():
                self.behavior_filter.append(self.behavior_list[selection])

    def evt_clear_filter_default(self, event):
        self.behavior_filter = []
        # self.behavior_list = []

    def evt_show_results(self, event):
        self.filtered_dataframe = self.dataframe[self.dataframe['duration'] >= self.min_duration]
        self.filtered_dataframe = self.filtered_dataframe[self.filtered_dataframe['mean_confidence'] >=
                                                          self.min_mean_confidence]
        if len(self.behavior_filter) > 0:
            self.filtered_dataframe = self.filtered_dataframe[
                self.filtered_dataframe['behavioral_sequence_name'].isin(self.behavior_filter)]

        if self.results:
            self.results.update_dataframe(self.filtered_dataframe)
            if self.results.IsShown():
                self.results.panel.Layout()
            else:
                self.results.Show()
        else:
            self.results = GridPage('Behavior Sequences', width=800, height=200)
            self.results.update_dataframe(self.filtered_dataframe)
            self.results.Show()
        self.behavior_list = list(self.filtered_dataframe['behavioral_sequence_name'].unique())
        self.behavior_list.sort()


# Run the program
if __name__ == '__main__':
    app = wx.App()
    BehaviorSequencesInitialWindow("Baker's Behavioral Sequence Detector Interface", mode='TEST')
    app.MainLoop()
