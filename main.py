import pandas as pd
import openpyxl


def cleanData(input):
    input = input.replace('[', '')
    input = input.replace(']', '')
    input = input.replace("'", '')
    input = input.replace(" ", '')
    cleanInput = input.split(',')
    return cleanInput

# Output file will include:
    # animal_ID: an integer starting at 0 that represents each individual animal in LabGym
    # behavioral_sequence_name: first_second_third...
    # behavioral_sequence_alias (optional): alias representing specific sequence of behaviors
    # mean_probability: averaged probabilities of each behavior
    # start_time: in seconds (to two decimal places)
    # end_time: in seconds (to two decimal places)


if __name__ == '__main__':
    # Make variables for later UI config
    # min_depth and max_depth which is number of behaviors in a row to consider
    file_name = "sequence_sample_data_test_cases.xlsx"
    min_depth = 2
    max_depth = 2

    # Read in Excel file
    data = pd.read_excel(file_name)
    '''print(data.columns[3])
    print(data.at[data.index[0], data.columns[31]])
    behavioral_sample = cleanData(data.at[data.index[0], data.columns[31]])
    print(behavioral_sample)
    print(behavioral_sample[1])
    print(behavioral_sample[0])'''

    # Make new Excel file to store info
    df = pd.DataFrame(columns=['animal_ID', 'behavioral_sequence_name', 'mean_probability',
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

        for col_index in range(1, data.shape[1] - 1):
            # Get the next two behavior/probability pairs to look at
            current_data_a = cleanData(str(data.at[data.index[i], data.columns[col_index]]))
            current_data_b = cleanData(str(data.at[data.index[i], data.columns[col_index + 1]]))
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
                # If they're equal, but you already have previous data to link
                elif temp_a != temp_b and continuing_behavior:
                    probability_sum += float(probability_b)
                    num_behavior_instances += 1
                # If the behaviors are different, but it's only just started
                elif temp_a != temp_b and first_seq:
                    start_time = data.columns[col_index]
                    probability_sum = float(probability_a) + float(probability_b)
                    num_behavior_instances = 2
                    behavior_a = temp_a
                    continuing_behavior = True
                # If the behaviors are different for the first time, set second behavior
                elif temp_a != temp_b and not continuing_sequence:
                    behavior_b = temp_b
                    num_behavior_instances += 1
                    probabilities_a = probability_sum
                    num_behavior_instances_a = num_behavior_instances
                    probability_sum = 0
                    continuing_sequence = True
                    behavioral_sequence_name = behavior_a + "_" + behavior_b
                # If the behaviors are different, and you want to end the previous sequence
                elif temp_a != temp_b and continuing_sequence:
                    num_behavior_instances += 1
                    probabilities_b = probability_sum
                    num_behavior_instances_b = num_behavior_instances
                    mean_probability = (probabilities_a + probabilities_b) / (num_behavior_instances_a + num_behavior_instances_b)
                    end_time = data.columns[col_index]
                    animal_ID = data.at[i, data.columns[0]]
                    # df1 = pd.DataFrame({"a": [1, 2, 3, 4],
                    #                   "b": [5, 6, 7, 8]})
                    new_data = {'animal_ID': animal_ID,
                                             'behavioral_sequence_name': behavioral_sequence_name,
                                             'mean_probability': mean_probability,
                                             'start_time': start_time, 'end_time': end_time}
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    continuing_sequence = False
                    continuing_behavior = False
                    num_behavior_instances -= 1
                    probability_sum = probabilities_b
                    behavior_a = behavior_b
                    col_index -= 1
                    start_time = end_time

                    # start_time is the time of first occurrence of a in series
                    # end_time is the column after last occurrence of b in series
            else:
                if continuing_sequence or continuing_behavior:
                    num_behavior_instances += 1
                    probabilities_b = probability_sum
                    behavior_b = temp_a
                    behavioral_sequence_name = behavior_a + "_" + behavior_b
                    num_behavior_instances_b = num_behavior_instances
                    mean_probability = (probabilities_a + probabilities_b) / (num_behavior_instances_a + num_behavior_instances_b)
                    end_time = data.columns[col_index]
                    animal_ID = data.at[i, data.columns[0]]
                    new_data = {'animal_ID': animal_ID,
                                'behavioral_sequence_name': behavioral_sequence_name,
                                'mean_probability': mean_probability,
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



    # Return list of behavioral sequences for each ID
        # Includes start time and end time of each behavior sequence occurrence
    # Write to an Excel file
    output_filename = './output_excel.xlsx'
    df.to_excel(output_filename, index=False)
