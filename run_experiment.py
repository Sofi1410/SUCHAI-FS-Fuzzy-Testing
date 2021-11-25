from randomsequencefuzzerwithfixedparams import RandomSequenceFuzzerWithFixedParams
from randomsequencefuzzerwithfixedparamsandexacttypes import RandomSequenceFuzzerWithFixedParamsAndExactTypes
from randomcommandsequencefuzzer import RandomCommandsSequenceFuzzer
from randomsequencefuzzer import RandomSequenceFuzzer
from flightsoftwarerunner import FlightSoftwareRunner
from subprocess import PIPE, Popen
import os
import pandas as pd
import json
import time
import argparse
import numpy as np

def to_json(information, iterations, t, json_path):
    """
    Write information to JSON file.
    :param information: Tuple with: list of commands, list of parameters, executed commands, command results,
            commands execution time, exit code of the process, total execution time, real memory used and
            virtual memory used of each iteration.
    :param iterations: Int.
    :param t: String. Start date and time of the execution.
    :param json_path: String. Directory where to write the JSON file.
    :return:
    """
    json_lst = []
    for iteration in range(iterations):
        iter_dic = dict()

        # Add information of each command sent
        cmds_lst = []
        results = information[iteration]
        cmds_sent = results[0]
        params_sent = results[1]
        for cmd_idx in range(len(cmds_sent)):
            cmds_lst.append({"cmd_name": cmds_sent[cmd_idx], "params": params_sent[cmd_idx]})
        iter_dic['cmds'] = cmds_lst

        # Add general information of the sequence
        iter_dic['exit code'] = results[5]
        iter_dic['total time (s)'] = results[6]  # Select a sequence, then the results of it, then the time
        iter_dic['virtual memory (kb)'] = results[8]
        iter_dic['real memory (kb)'] = results[7]
        json_lst.append(iter_dic)

    # Write to json
    filename = 'data-' + t + '.txt'
    if not os.path.exists(json_path):
        os.mkdir(json_path)
    with open(json_path + filename, 'w') as outfile:
        json.dump(json_lst, outfile, indent=2, separators=(',', ': '))


def to_csv_file(information, iterations, t, csv_path):
    """
    Write information to CSV file.
    :param information: Tuple with: list of commands, list of parameters, executed commands, command results,
            commands execution time, exit code of the process, total execution time, real memory used and
            virtual memory used of each iteration.
    :param iterations: Int.
    :param t: String. Start date and time of the execution.
    :param csv_path: String. Directory where to write the CSV file.
    :return:
    """
    csv_lst = []
    for iteration in range(iterations):
        # Add information of each command sent
        csv_lst.append([])
        results = information[iteration]
        cmds_sent = results[0]
        params_sent = results[1]
        for j in range(len(cmds_sent)):
            csv_lst[iteration].append(cmds_sent[j])
            csv_lst[iteration].append("'" + params_sent[j] + "'")

        # Add general information of the sequence
        csv_lst[iteration].append(results[5])
        csv_lst[iteration].append(results[6])
        csv_lst[iteration].append(results[8])
        csv_lst[iteration].append(results[7])

    cols = []
    number_of_commands = len(information[0][0])

    # Add columns
    for cmd_idx in range(number_of_commands):
        cols.append("Command")
        cols.append("Parameters")
    cols.append("Exit Code")
    cols.append("Total Time")
    cols.append("Virtual Memory (kB)")
    cols.append("Real Memory (kB)")

    # Create dataframe and write to CSV file
    information_df = pd.DataFrame(csv_lst, columns=cols)
    filename = 'data-' + t + '.csv'
    if not os.path.exists(csv_path):
        os.mkdir(csv_path)
    information_df.to_csv(csv_path + filename, index=False)


def run_experiment(random_fuzzer, iterations=10, cmds_number=10, csv_path='', json_path=''):
    """
    Create a random fuzzer instance to execute flight software with random input.
    :param random_fuzzer: Class. Fuzzer.
    :param iterations: Int.
    :param cmds_number: Int. Number of commands to execute each iteration.
    :param csv_path: String. Directory for CSV reports. The directory must exist. Must end with a "/" character.
    :param json_path: String. Directory for JSON reports. The directory must exist. Must end with a "/" character.
    :return:
    """
    print("Commands number: " + str(cmds_number) + ", iteration: " + str(iterations))

    # print(params_type)
    # Run zmqhub.py (ipc)
    # ex_zmqhub = Popen(["python3", "zmqhub.py", "--ip", "/tmp/suchaifs", "--proto", "ipc"], stdin=PIPE)
    # Run zmqhub.py (tcp)
    ex_zmqhub=None
    try:
        ex_zmqhub = Popen(["python3", "zmqhub.py", "--mon", "-i", "8002", "-o", "8001","-m", "80002"], stdin=PIPE)
        print(os.path)
        exec_dir = "../SUCHAI-Flight-Software/build/apps/simple/"
        exec_cmd = "./suchai-app"  #aca le doy el nombre del ejecutable
        # Run flight software sending n_cmds random commands with 1 random parameter
        prev_dir = os.getcwd()
        os.chdir(exec_dir)
        start_time = time.strftime("%Y%m%d-%H%M%S")  # Measure start time to include it in the report name
        outcomes = random_fuzzer.runs(FlightSoftwareRunner(exec_cmd=exec_cmd), iterations)
        os.chdir(prev_dir)
    except KeyboardInterrupt:
        pass

    finally:
        ex_zmqhub.kill()
    # Write outcome information report

    # TODO revisar outcomes y buscar por 0s en las tuplas
    #el payload es : mds_list, params_list, executed_cmds, results, cmds_time, return_code, total_exec_time, rm, vm
    #nos interesa return code   



    to_json(outcomes, iterations, start_time, json_path)

    # Write report to csv file
    to_csv_file(outcomes, iterations, start_time, csv_path)
    # Set variables
    print("OUTCOME -")
    #print(outcomes)
    print("OUTCOME -> RETURN_VALUE")
    result=[]
    for seq in outcomes:
        print(seq[5])
        result.append(seq[5])
    final=np.array(result)
    return not final.all()          #arroja FALSE si al menos 1 es 0
        

     

    


def get_parameters():
    """
    Parse script arguments.
    Every path argument must end with a "/".
    """
    parser = argparse.ArgumentParser(prog='run_experiment.py')

    parser.add_argument('--csv_path', type=str, default='Dummy-Folder/CSV/', help="Save CSV reports in this directory")
    parser.add_argument('--json_path', type=str, default='Dummy-Folder/JSON/', help="Save JSON reports in this directory")
    parser.add_argument('--time_path', type=str, default='Dummy-Folder/Time/', help="Save time reports in this directory")
    parser.add_argument('--iterations', nargs='+', type=int, default="10 100 500 1000", help="Number of sequences")
    parser.add_argument('--commands_number', nargs='+', type=int, default="5 10 50 100", help="Number of commands in a "
                                                                                              "sequence")
    parser.add_argument('--min_length', type=int, default=0, help="Minimum length of the random command names.")
    parser.add_argument('--max_length', type=int, default=10, help="Maximum length of the random command names.")
    parser.add_argument('--char_start', type=int, default=33, help="Index of the range that indicates where to start "
                                                                   "producing random command names in ASCII code.")
    parser.add_argument('--char_range', type=int, default=93, help="Length of the characters range in ASCII code.")
    parser.add_argument('--strategy', type=int, default=0, help="Number of the strategy to be run")
    parser.add_argument('--commands_file', type=str, default='suchai_cmd_list_all.csv', help="Filename with the SUCHAI "
                                                                                             "Flight Software commands "
                                                                                             "and parameters type.")

    return parser.parse_args()


def main(time_path, csv_path, json_path, iterations, commands_number, min_length, max_length, char_start, char_range, fuzz_class, commands_file):
    """
    :param time_path: Directory for time reports. The directory must exist. Must end with a "/" character.
    :param csv_path: Directory for CSV reports. The directory must exist. Must end with a "/" character.
    :param json_path: Directory for JSON reports. The directory must exist. Must end with a "/" character.
    :param iterations: List. Each element represents a sequences' number.
    :param commands_number: List. Each element represents a commands' number in a sequence.
    :param min_length: Int. Minimum length of the random command names.
    :param max_length: Int. Maximum length of the random command names.
    :param char_start: Int. Index of the range that indicates where to start producing random command names in ASCII code.
    :param char_range: Int. Length of the characters range in ASCII code.
    :param fuzz_class: Class. Fuzzer class to be used.
    :param commands_file: String. Filename with the SUCHAI Flight Software commands and parameters type.
    :return:
    """
    # Create file to write execution time for each iteration
    curr_time = time.strftime("%Y%m%d-%H%M%S")

    if not os.path.exists(time_path):
        os.mkdir(time_path)

    f = open(time_path + 'exec_time-' + curr_time + '.txt', '+w')
    f.close()

    return_list=[]
    # Run experiment and add execution time of each iteration to time reports
    for num_cmds in commands_number:

        # Create fuzzer instance
        fuzzer = fuzz_class(commands_file, min_length=min_length, max_length=max_length, char_start=char_start,
                            char_range=char_range, n_cmds=num_cmds)

        for iter in iterations:
            exec_start_time = time.time()
            return_list.append(run_experiment(fuzzer, int(iter), int(num_cmds), csv_path, json_path))
            with open(time_path + 'exec_time-' + curr_time + '.txt', 'a') as f:
                f.write("%s\n" % (time.time() - exec_start_time))
    return return_list


if __name__ == "__main__":
    args = get_parameters()
    strategies_fuzz_classes = {0: RandomCommandsSequenceFuzzer,
                               1: RandomSequenceFuzzer,
                               2: RandomSequenceFuzzerWithFixedParams,
                               3: RandomSequenceFuzzerWithFixedParamsAndExactTypes}
    return_codes=main(args.time_path, args.csv_path, args.json_path, args.iterations, args.commands_number, args.min_length, args.max_length, args.char_start, args.char_range, strategies_fuzz_classes[args.strategy], args.commands_file)
    print(return_codes)
    result=np.array(return_codes)
    exit(not result.all())  #true if all values are 0



