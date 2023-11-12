import pandas as pd
import openpyxl  # added this line to ensure openpyxl is installed. It throws a useful error.


# This function takes the input sample format [name, confidence], cleans it (removing unnecessary characters),
# and returns two values: behavior and confidence
def cleanup_data_sample(sample):
    sample = sample.replace('[', '')
    sample = sample.replace(']', '')
    sample = sample.replace("'", "")
    sample = sample.split(',')
    return sample[0], float(sample[1])

# This function takes in a dataframe with a single row. It combines any repeating instances of a behavior
# into a single item with a single start/end time and averages (mean) the confidence. This reduces the complexity
# of finding sequence of different behaviors later in our process. It returns the data as an array (list of lists)
# where each row is a different behavior, confidence, start, end
# note: NA is a "valid" option for this process and will be kept. It is needed later in the process.
def make_behavior_list(df_row_input, animal_id):
    return_behavior_list = []
    first = True
    start_time = 0
    end_time = 0
    done = False
    # loop through every iterm in the row. condense any behaviors that span multiple time samples into
    # a single behavior with a new start/end time.
    while not done:
        behavior_sample = df_row_input.at[df_row_input.index[0], df_row_input.columns[0]]
        behavior, confidence = cleanup_data_sample(behavior_sample)
        current_time = float(df_row_input.columns[0])
        if first:
            first = False
            start_time = current_time
            previous_behavior = behavior
            confidence_total = 0
            count_of_behavior = 0
        if behavior == previous_behavior:
            end_time = current_time
            confidence_total += confidence
            count_of_behavior += 1

            # remove the current column from the dataframe.
            df_row_input = df_row_input.drop(columns=[df_row_input.columns[0]])

            # catch the case where that was the last item in the row
            if df_row_input.empty:
                if len(return_behavior_list) > 0:
                    return_behavior_list += ([animal_id, behavior, confidence, start_time, end_time], )
                else:
                    return_behavior_list.append([animal_id, behavior, confidence, start_time, end_time], )
                done = True
        else:
            confidence = confidence_total / count_of_behavior

            # store the result when you find a full single, behavior.
            return_behavior_list.append([animal_id, previous_behavior, confidence, start_time, end_time],)

            # recursive call to this function sending the reduced size (column removed) dataframe.
            # it will keep calling itself until the dataframe is empty and then start climbing back up the
            # recursion stack
            return_behavior_list += make_behavior_list(df_row_input, animal_id)
            done = True
            # this is an alternate way to make it be "done". empty the dataframe and do while no dataframe.empty
            #df_row_input = df_row_input.iloc[0:0]
    return return_behavior_list


# Function to find a sequence of length "sequence_length" and return the correct list of values
def find_sequence(input_list, sequence_length):
    # format of input_list is: [animal_id, behavior, confidence, start_time, end_time]
    individual_behaviors_list = []
    name = input_list[0][1]
    confidence = input_list[0][2]
    start_time = input_list[0][3]
    end_time = input_list[0][4]

    # make a list containing the data for each individual behavior in the sequence. Any relevant data can be
    # added here.
    individual_behaviors_list.append([name, round(float(confidence), 4),
                                      float(start_time),
                                      float(end_time)], )
    for behavior_row in input_list[1:]:
        name += "_" + behavior_row[1]
        confidence += behavior_row[2]
        individual_behaviors_list.append([behavior_row[1], round(behavior_row[2], 4),
                                          float(behavior_row[3]),
                                          float(behavior_row[4])], )
        end_time = float(behavior_row[4])

    # return value is [animal_id, sequence length, sequence_name, mean_confidence
    #                   sequence_start_time, sequence_end_time,
    #                   sequence duration, [list of data for individual behaviors in sequence]
    #
    # the list of data for individual behaviors includes: name, start_time, end_time
    return [input_list[0][0], sequence_length, name,
            round(confidence / sequence_length, 4), start_time,
            end_time, round(end_time - start_time, 4),
            individual_behaviors_list]


# This function takes a Row from a dataframe containing behavior samples, simplifies it using
# make_behavior_list, finds that sequences in range min/max, and returns an array (list of lists) containing
# the valid sequences found in that row
def process_single_row(df_row, behaviors_min, behaviors_max):
    animal_id = df_row.at[df_row.index[0], df_row.columns[0]]
    behavior_list = make_behavior_list(df_row.drop(columns=[df_row.columns[0]]), animal_id)
    row_behaviors_array = []
    while len(behavior_list) >= behaviors_min:
        for length in range(behaviors_min, behaviors_max+1):

            # This is a complex lines, but it looks through the sub array to determine
            # if "NA" is anywhere in it.  If "NA" is within the array, there is no reason
            # process it because a valid sequence will not be found
            NA_in_set = any("NA" in sublist for sublist in behavior_list[0:length])
            if not NA_in_set and len(behavior_list[0:length]) == length:
                sequence = find_sequence(behavior_list[0:length], length)
                row_behaviors_array.append(sequence)
            else:
                # if we found an "NA" in the subset of the array to be analyzed,
                # then there's no point in continuing. No More sequences exist
                break
        behavior_list.pop(0)
    return row_behaviors_array

# Function processes the entire input file and return an array containing the behavior sequences within the dataset
def find_all_sequences(input_data, behavior_size_min, behavior_size_max):
    data_array = []

    # Make and empty dataframe with the correct column header (aka sample times)
    single_row_df = pd.DataFrame(columns=input_data.columns)

    # process a single row at a time looping through all rows of data.  Each row is 1 animal ID
    for row_index in range(input_data.shape[0]):

        # Set the data for the individual row to the current row in the overall dataset
        single_row_df.loc[1] = input_data.loc[row_index].copy()

        # find the sequences in a single row
        temp = process_single_row(single_row_df, behavior_size_min, behavior_size_max)

        # if a valid sequence is found, store it and then continue
        if len(temp) > 0:
            data_array.append(temp)

    return data_array

# This function creates an empty dataframe with the appropriate columns based on the min/max sequence input
def make_empty_return_dataframe(max_behaviors):
    output_df_columns = ['animal_id',
                         'behavior_count',
                         'behavioral_sequence_name',
                         'mean_confidence',
                         'start_time',
                         'end_time',
                         'duration']
    for index in range(1, max_behaviors + 1):
        output_df_columns.append(f"behavior_{index}")
        output_df_columns.append(f"behavior_{index}_mean_confidence")
        output_df_columns.append(f"behavior_{index}_start")
        output_df_columns.append(f"behavior_{index}_end")
        output_df_columns.append(f"behavior_{index}_duration")
    return pd.DataFrame(columns=output_df_columns)

# This function takes an input file path and the min/max individual behaviours
# that define a sequences and steps through the process of finding the behavior sequences in the dataset
def process_file(input_filename, behaviors_min, behaviors_max):
    # read in the data from an Excel file
    df_from_file = pd.read_excel(input_filename)

    # create the dataframe to return that includes the appropriate number of behavior columns
    return_dataframe = make_empty_return_dataframe(behaviors_max)

    # given the input data, return a simple array that contains all the detected behavior sequences and their details
    results_df = find_all_sequences(df_from_file, behaviors_min, behaviors_max)

    # unpack the behavior array and put it into a dataframe for further analysis and to return to a file
    return_dataframe = convert_behavior_array_to_dataframe(results_df, return_dataframe)

    return return_dataframe

# This function takes in an array of data containing all the sequences
# found in the dataset. It returns the pandas dataframe format of those sequences.
def convert_behavior_array_to_dataframe(behavior_array, output_dataframe):
    entry_counter = 0
    for length_index in range(len(behavior_array)):
        for index, behavior_set in enumerate(behavior_array[length_index]):
            df_temp = {'animal_id': int(behavior_set[0]),  # animal_id
                       'behavior_count': behavior_set[1],  # behavior_counter
                       'behavioral_sequence_name': behavior_set[2],  # behavior_name
                       'mean_confidence': behavior_set[3],  # round(confidence_sum / (sample_index + 1), 4)
                       'start_time': behavior_set[4],  # behavior_start_time
                       'end_time': behavior_set[5],  # current_time
                       'duration': behavior_set[6]}  # round(current_time - behavior_start_time, 4)
            # Index is adjusted to give behavior names starting with 1, then 2, then 3, etc. instead of starting at 0
            for index_df_temp in range(1, behavior_set[1]+1):
                df_temp[f"behavior_{index_df_temp}"] = behavior_set[7][index_df_temp-1][0]
                df_temp[f"behavior_{index_df_temp}_mean_confidence"] = behavior_set[7][index_df_temp-1][1]
                df_temp[f"behavior_{index_df_temp}_start"] = behavior_set[7][index_df_temp-1][2]
                df_temp[f"behavior_{index_df_temp}_end"] = behavior_set[7][index_df_temp-1][3]
                df_temp[f"behavior_{index_df_temp}_duration"] = round((behavior_set[7][index_df_temp-1][3] -
                                                                       behavior_set[7][index_df_temp-1][2]), 4)
            output_dataframe.loc[entry_counter] = df_temp
            entry_counter += 1
        # replace any empy (aka NAN) value with a blank string in the dataframe for readability
        output_dataframe = output_dataframe.fillna('')
    return output_dataframe

# This is a simple function call to save the pandas dataframe containing sequences to an Excel file.
def save_results_to_excel(dataframe, output_filename):
    dataframe.to_excel(output_filename, index=False)
    return


# Press the green button in the gutter to run the script. This is only to test the backend
# independent of the User Interface
if __name__ == '__main__':
    input_file = 'test-files/all_events-1.xlsx'
    output_file = './output_excel.xlsx'
    minimum_behaviors_in_a_set = 2
    maximum_behaviors_in_a_set = 2
    results_dataframe = process_file(input_file, minimum_behaviors_in_a_set, maximum_behaviors_in_a_set)
    save_results_to_excel(results_dataframe, output_file)