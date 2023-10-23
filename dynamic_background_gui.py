import os
import wx
import threading
import pandas as pd
from pathlib import Path
import platform, subprocess


# Class: DynamicBackgroundInitialWindow
# Description: This class was taken from LabGym and then modified for User input
class DynamicBackgroundInitialWindow(wx.Frame):

    def __init__(self, title, mode='MIN'):
        wx.Frame.__init__(self, parent=None, title=title)
        self.panel = DynamicBackgroundPanel(self, mode=mode)
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.frame_sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(self.frame_sizer)
        self.Size = (self.panel.BestVirtualSize[0] + 30, self.panel.BestVirtualSize[1] + 40)
        self.Move(wx.Point(50, 50))
        self.Show()


class DynamicBackgroundPanel(wx.ScrolledWindow):

    def __init__(self, parent, mode='TEST'):
        wx.ScrolledWindow.__init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize,
                                   style=wx.HSCROLL | wx.VSCROLL,
                                   name="scrolledWindow")
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
        # self.sequence_length.Disable()

        # Process those sequences
        self.process_sequences_button = wx.Button(self, label='Process Sequences')
        self.process_sequences_button.Bind(wx.EVT_BUTTON, self.evt_process_sequences)

        # Filters (confidence and ...name?)
        # self.filter_confidence_button = wx.Button(self, label='Filter Sequences')
        # self.filter_confidence_button.Bind(wx.EVT_BUTTON, self.evt_filter_confidence)

        # Done button and closing everything
        save_button = wx.Button(self, label='Save')
        save_button.Bind(wx.EVT_BUTTON, self.evt_save_results)

        view_results_file_button = wx.Button(self, label='View Results File')
        view_results_file_button.Bind(wx.EVT_BUTTON, self.evt_open_result_file)

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
        """
        # Add the inference size widgets in their own row.
        inference_size_box = wx.StaticBox(self)
        inference_size_sizer = wx.StaticBoxSizer(inference_size_box, wx.VERTICAL)

        inference_size_sizer.Add(self.inference_size_text, flag=wx.ALIGN_CENTER_HORIZONTAL)

        inference_size_sizer.Add(self.inference_size_widget, flag=wx.ALIGN_CENTER_HORIZONTAL)

        model_parameter_options.Add(inference_size_sizer, flag=wx.ALIGN_CENTER)
        model_parameter_options.Add(5, 0)

        # Add the threshold selection widgets in their own row.
        detection_threshold_box = wx.StaticBox(self)
        detection_threshold_sizer = wx.StaticBoxSizer(detection_threshold_box, wx.VERTICAL)

        detection_threshold_sizer.Add(self.detection_threshold_text, flag=wx.ALIGN_CENTER_HORIZONTAL)

        detection_threshold_sizer.Add(self.detection_threshold_widget, flag=wx.ALIGN_CENTER_HORIZONTAL)

        model_parameter_options.Add(detection_threshold_sizer, flag=wx.ALIGN_CENTER)
        model_parameter_options.Add(5, 0)
        """

        # Add the model options to the vertical window container
        overall_window_vertical.Add(get_input_options_vertical, flag=wx.EXPAND)

        overall_window_vertical.Add(0, 5)
        # Place the "Process image" button
        process_sequence_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        process_sequence_button_sizer.Add(10, 0)
        process_sequence_button_sizer.Add(self.process_sequences_button, wx.LEFT)

        # Add the image options to the vertical window container
        overall_window_vertical.Add(process_sequence_button_sizer)

        ###### End of Step 3 GUI
        save_button_horizontal = wx.BoxSizer(wx.HORIZONTAL)

        save_box = wx.StaticBox(self)
        save_sizer = wx.StaticBoxSizer(save_box, wx.VERTICAL)
        save_sizer.Add(save_button)
        save_sizer.Add(0, 5)
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
        min_depth = 2
        max_depth = 2

        # Read in Excel file
        data = pd.read_excel(file_name)

        # Make new Excel file to store info
        df = pd.DataFrame(columns=['animal_ID', 'behavioral_sequence_name', 'mean_confidence',
                                   'start_time', 'end_time'])

        # First row is time
        # First column is animal ID (row.name is animal ID)
        # Each behavior is ['behavior_name', probability of behavior]
        # Each row is the series of behaviors

        # Go through each row of the file, starting with row two (animal ID 0)
        for i in range(data.shape[0]):
            continuing_behavior = False
            continuing_sequence = False
            probability_sum = 0
            probabilities_a = 0
            probabilities_b = 0
            num_behavior_instances = 0
            num_behavior_instances_a = 0
            num_behavior_instances_b = 0
            behavior_a = ""
            behavior_b = ""
            start_time = 0
            behavioral_sequence_name = ""
            first_seq = True
            col_index = 1

            while col_index < (data.shape[1] - 1):
                # Get the next two behavior/probability pairs to look at
                current_data_a = self.cleanData(str(data.at[data.index[i], data.columns[col_index]]))
                current_data_b = self.cleanData(str(data.at[data.index[i], data.columns[col_index + 1]]))
                temp_a, probability_a = current_data_a
                temp_b, probability_b = current_data_b

                # Starting a sequence
                # If the behavior (a) is not 'NA' and the next behavior (b) is not 'NA'
                if temp_a != "NA" and temp_b != "NA":
                    # If behavior (a) is the same as behavior (b), for the first time
                    if temp_a == temp_b and not continuing_behavior and not continuing_sequence:
                        continuing_behavior = True
                        start_time = data.columns[col_index]
                        probability_sum = float(probability_a) + float(probability_b)
                        num_behavior_instances = 2
                        behavior_a = temp_a
                        first_seq = False
                    # If they're equal, but you already have previous data to link
                    elif temp_a == temp_b and continuing_behavior:
                        probability_sum += float(probability_b)
                        num_behavior_instances += 1
                        first_seq = False
                    # If the behaviors are different, but it's only just started
                    elif temp_a != temp_b and first_seq:
                        start_time = data.columns[col_index]
                        if num_behavior_instances > 0:
                            probabilities_a = probability_sum
                            num_behavior_instances_a = num_behavior_instances
                        else:
                            probabilities_a = float(probability_a)
                            num_behavior_instances_a = 1
                        num_behavior_instances = 1
                        probability_sum = float(probability_b)
                        behavior_a = temp_a
                        behavior_b = temp_b
                        behavioral_sequence_name = behavior_a + "_" + behavior_b
                        continuing_behavior = True
                        continuing_sequence = True
                        first_seq = False
                    # If the behaviors are different for the first time, set second behavior
                    elif temp_a != temp_b and not continuing_sequence:
                        behavior_b = temp_b
                        probabilities_a = probability_sum
                        num_behavior_instances_a = num_behavior_instances
                        num_behavior_instances = 1
                        probability_sum = float(probability_b)
                        continuing_sequence = True
                        behavioral_sequence_name = behavior_a + "_" + behavior_b
                        first_seq = False
                    # If the behaviors are different, and you want to end the previous sequence
                    elif temp_a != temp_b and continuing_sequence:
                        probabilities_b = probability_sum
                        num_behavior_instances_b = num_behavior_instances
                        mean_probability = (probabilities_a + probabilities_b) / (
                                    num_behavior_instances_a + num_behavior_instances_b)
                        end_time = data.columns[col_index]
                        animal_ID = data.at[i, data.columns[0]]
                        new_data = {'animal_ID': animal_ID,
                                    'behavioral_sequence_name': behavioral_sequence_name,
                                    'mean_confidence': mean_probability,
                                    'start_time': start_time, 'end_time': end_time}
                        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        continuing_sequence = False
                        continuing_behavior = False
                        behavior_a = behavior_b
                        col_index -= 1
                        start_time = end_time
                        first_seq = True

                        # start_time is the time of first occurrence of a in series
                        # end_time is the column after last occurrence of b in series
                else:
                    if continuing_sequence or continuing_behavior:
                        probabilities_b = probability_sum
                        behavior_b = temp_a
                        behavioral_sequence_name = behavior_a + "_" + behavior_b
                        num_behavior_instances_b = num_behavior_instances
                        mean_probability = (probabilities_a + probabilities_b) / (
                                    num_behavior_instances_a + num_behavior_instances_b)
                        end_time = data.columns[col_index]
                        animal_ID = data.at[i, data.columns[0]]
                        new_data = {'animal_ID': animal_ID,
                                    'behavioral_sequence_name': behavioral_sequence_name,
                                    'mean_confidence': mean_probability,
                                    'start_time': start_time, 'end_time': end_time}
                        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        continuing_sequence = False
                        continuing_behavior = False
                        num_behavior_instances -= 1
                        probability_sum = probabilities_b
                        behavior_a = behavior_b
                        col_index -= 1
                        start_time = end_time
                    continuing_behavior = False
                    continuing_sequence = False
                    probability_sum = 0
                    probabilities_a = 0
                    probabilities_b = 0
                    num_behavior_instances = 0
                    num_behavior_instances_a = 0
                    num_behavior_instances_b = 0
                    behavior_a = ""
                    behavior_b = ""
                    behavior_a_start_time = 0
                    behavior_b_end_time = 0
                    behavioral_sequence_name = ""
                    first_seq = True
                col_index += 1

            if continuing_sequence or continuing_behavior:
                probabilities_b = probability_sum
                behavior_b = temp_b
                behavioral_sequence_name = behavior_a + "_" + behavior_b
                num_behavior_instances_b = num_behavior_instances
                mean_probability = (probabilities_a + probabilities_b) / (
                        num_behavior_instances_a + num_behavior_instances_b)
                end_time = data.columns[data.shape[1] - 1]
                animal_ID = data.at[i, data.columns[0]]
                new_data = {'animal_ID': animal_ID,
                            'behavioral_sequence_name': behavioral_sequence_name,
                            'mean_confidence': mean_probability,
                            'start_time': start_time, 'end_time': end_time}
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                continuing_sequence = False
                continuing_behavior = False
                num_behavior_instances -= 1
                probability_sum = probabilities_b
                behavior_a = behavior_b
                col_index -= 1
                start_time = end_time

        # Return list of behavioral sequences for each ID
        # Includes start time and end time of each behavior sequence occurrence
        # Write to an Excel file
        # output_filename = str(self.get_input_label)
        self.dataframe = df

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
            self.dataframe.to_excel(filename, index=False)

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
            dlg = wx.GenericMessageDialog(None, 'No input file has been selected!', caption='Error', style=wx.OK | wx.CENTER)
            dlg.ShowModal()
            return
        if not self.sequence_length:
            dlg = wx.GenericMessageDialog(None, 'No sequence length has been selected!', caption='Error',
                                          style=wx.OK | wx.CENTER)
            dlg.ShowModal()
            return

        thread = threading.Thread(target=self.get_behavioral_sequences)
        thread.run()

    def evt_filter_confidence(self, event):
        if not self.min_confidence:
            dlg = wx.GenericMessageDialog(None, 'No minimum confidence has been selected!', caption='Error', style=wx.OK | wx.CENTER)
            dlg.ShowModal()
            return

        # ADD FILTERING IN
        thread = threading.Thread(target=self.get_behavioral_sequences)
        thread.run()

# Run the program
if __name__ == '__main__':
    app = wx.App()
    DynamicBackgroundInitialWindow("Baker's Behavioral Sequence Detector Interface", mode='TEST')
    app.MainLoop()
