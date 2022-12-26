import os
import sys
import json
import logging
import subprocess

log = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)

def info(msg):
    log.info(msg)

def warning(msg):
    log.warning(msg)

def exit_and_fail(msg):
    """This function logs the given error, and then exits with a 1 exit code."""
    if msg:
        log.error(msg)
    sys.exit(1)

def run_cmd(working_directory, cmd):
    """This function runs the given command in the given working directory."""
    # log.info("Execute: " + cmd)
    try:
        # output = subprocess.run(cmd, cwd=working_directory, shell=True, capture_output=True, check=True)
        output = subprocess.check_output(cmd, cwd=working_directory, shell=True)
    except subprocess.CalledProcessError as error:
        exit_and_fail("Command execution failed: %s. Output: %s" % (cmd, error))
    # log.info("--OUT--")
    # log.info(output)
    # log.info("--END--")
    return output
  

def convert_json_to_dict(obj):
    output = {}
    if type(obj) == str:
        try:
            output = json.loads(obj)
        except ValueError:
            # warning(f"The provided string '{obj}' has not json format")
            return str(obj)
    else:
        try:
            output = json.load(obj)
        except ValueError:
            exit_and_fail(f"The object {obj} has not json format")
    return output


def analyze_file_name(file_name=None) -> dict:
    name_dict = {}
    if file_name != None:
        name_dict['file_name'] = file_name
        file_name_splitName = file_name.split('_')
        pod_name = file_name_splitName[0]
        name_dict['pod_name'] = pod_name
        pod_name_split = pod_name.split('-')
        if pod_name_split[len(pod_name_split)-1].isdigit() or "eric-log-shipper" in file_name or "eric-cm-mediator-key-init" in file_name:
            length = len(pod_name_split)-1
        else:
            length = len(pod_name_split)-2
        service_name = ""
        for i in range(0,length):
            service_name += pod_name_split[i]+'-'
        name_dict['service_name'] = service_name[:len(service_name)-1]
        if len(file_name_splitName) == 3:
            container_name = file_name_splitName[1]
        else:
            container_name = file_name_splitName[1].split('.')[0]
        name_dict['container_name'] = container_name
    return name_dict


def get_files_from_folder(folder_path:str) -> list:
    if not os.path.exists(folder_path):
        exit_and_fail(f"Directory '{folder_path}' does not exist")
    if folder_path == None:
        exit_and_fail("No folder provided")
    if len(os.listdir(folder_path)) == 0:
        warning(f"Folder {folder_path} is empty")
        return []
    output = run_cmd(folder_path, "ls -p | grep -v /")
    files = str(output).split("'")[1].split('\\n')
    info(f"Files from '{folder_path}' have been extracted")
    return files[:len(files)-1]


def create_folder(directory:str, folder_name:str) -> None:
    l = len(folder_name)
    if folder_name[l-1] == '/':
        folder_name = folder_name[:l-1]
    if not os.path.exists(directory + folder_name):
        run_cmd(directory, f"mkdir {folder_name}")
        # info(f"A new folder '{folder_name}' has successfully been created in '{directory}'")
    else:
        info(f"Folder '{folder_name}' already exists in '{directory}")


def write_logs_to_file(folder_path:str, file_name:str, logs:list, start_index=None, end_index=None) -> None:
    if len(logs) <= 0: # create an empty file
        run_cmd(folder_path, f"touch {file_name}")
    else:   
        if start_index == None and end_index == None:
            start_index = 0
            end_index = len(logs)-1
        try:
            with open(folder_path + file_name, 'w') as logFile:
                logFile.write('[\n')
                for index in range(start_index, end_index):
                    logFile.write(json.dumps(logs[index].convert_to_dict(), indent=2) + ',\n')
                logFile.write(json.dumps(logs[end_index].convert_to_dict(), indent=2) + '\n')
                logFile.write(']')
        except EnvironmentError as error:
            exit_and_fail(f"Failed to open '{folder_path}{file_name}' file in writing mode with error message: \n{error}")


def read_logs_from_file(folder_path:str, file_name:str, reading_mode:str) -> list:
    try:
        with open(folder_path + file_name, 'r') as logFile:
            logs = []
            if reading_mode == "obj": # read file as object (i.e. it may a list of dictionaries)
                logs = convert_json_to_dict(logFile) 
            elif reading_mode == "line": # read file line-by-line
                for line in logFile:
                     if line == "\n": continue # omit the empty lines
                     logs.append(line)
            else:
                exit_and_fail("The reading mode can be either 'obj' or 'line'")
    except EnvironmentError as error:
        exit_and_fail(f"Failed to open '{folder_path}{file_name}' file in reading mode with error message: \n{error}")
    return logs