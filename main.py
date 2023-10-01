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
    file_name = "all_events-1.xlsx"
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
        continuing_sequence = True
        probability_sum = 0
        num_behavior_instances = 0
        behavior_a = ""
        behavior_b = ""

        for col_index in range(1, data.shape[1] - 1):       # --> data.shape[1] is the # of columns
            current_data_a = cleanData(str(data.at[data.index[i], data.columns[col_index]]))
            current_data_b = cleanData(str(data.at[data.index[i], data.columns[col_index + 1]]))
            temp_a, probability_a = current_data_a
            temp_b, probability_b = current_data_b

            # If the behavior (a) is not 'NA' and the next behavior (b) is not 'NA'
            if temp_a != "NA" and temp_b != "NA":
                # If behavior (a) is the same as behavior (b), for the first time
                if temp_a == temp_b and not continuing_behavior:
                    continuing_behavior = True
                    start_time = data.columns[col_index]
                    probability_sum = probability_a + probability_b
                    num_behavior_instances = 2
                elif temp_a == temp_b and continuing_behavior:
                    probability_sum += probability_b
                    num_behavior_instances += 1
                # If the behaviors are different, but this is a sequence
                elif continuing_sequence:
                    # Add a_b to the behavioral_sequence_name
                    continuing_behavior = False
                    behavioral_sequence_name = temp_a + "_" + temp_b
                    # If alias exists, add to behavioral_sequence_alias, else "unknown"
                    # Compute mean_probability for a and b
                # If the behaviors are different, and you want to end the previous sequence
                elif not continuing_sequence:
                    mean_probability = (probability_sum) / num_behavior_instances
                    end_time = data.columns[col_index + 1]
                    animal_ID = data.at[i, data.columns[0]]
                    new_data = {animal_ID, behavioral_sequence_name, mean_probability, start_time, end_time}
                    df = df.append(new_data)
                    # start_time is the time of first occurrence of a in series
                    # end_time is the column after last occurrence of b in series
            else:
                continuing_behavior = False
                continuing_sequence = True
                probability_sum = 0
                num_behavior_instances = 0


    # Return list of behavioral sequences for each ID
        # Includes start time and end time of each behavior sequence occurrence
    # Write to an Excel file
    df.to_csv('file1.csv')
