#!/usr/bin/env python3.10

import yaml
from common_functions import * 
from LogAnalysis import *

def main():

    default_folder = "/logAnalysis/.logChecker/"
    cwd = os.getcwd()
    info("Current working directory: " + cwd)

    log_checker_folder = cwd + "/.logChecker/"
    if (not os.path.exists(log_checker_folder)):
        run_cmd(cwd, f"mkdir -p {log_checker_folder}")
        run_cmd(cwd, f'cp -r {default_folder+"*"} {log_checker_folder}')
    else:
        if "configuration.yml" not in os.listdir(log_checker_folder):
            conf_file = default_folder + "configuration.yml"
            run_cmd(cwd, f"cp {conf_file} {log_checker_folder}")
        if (not os.path.exists(log_checker_folder + "data/")) or (len(os.listdir(log_checker_folder + "data/")) == 0):
            data_folder = default_folder + "data/"
            run_cmd(cwd, f"cp -r {data_folder} {log_checker_folder}")
        if os.path.exists(log_checker_folder + "results/"):
            results_folder = log_checker_folder + "results/"
            run_cmd(cwd, f"rm -rf {results_folder}")

    results_folder = log_checker_folder + "results/"
    run_cmd(cwd, f"mkdir -p {results_folder}")

    input_folder = log_checker_folder + "data/"
    output_folder = log_checker_folder + "results/"

    with open(log_checker_folder + "configuration.yml", 'r') as stream:
        try:
            conf = yaml.safe_load(stream)
        except yaml.YAMLError as error:
            exit_and_fail(f"Cannot read configuration file\n\t{error}")       

    log_analysis = LogAnalysis(input_folder)
    log_analysis.create_container_folders(output_folder)
    log_analysis.fetch_logs(input_folder)

    anal_conf = conf['analysis']

    valid_conf_dict = anal_conf['validation']
    if type(valid_conf_dict['enabled'])==bool: 
        if valid_conf_dict['enabled']:
            log_analysis.validation_analysis()
    else:
        exit_and_fail("Validation enabled parameter should be of type boolean")

    rate_conf_dict = anal_conf['rate']
    rate_enabled = rate_conf_dict['enabled']
    rate_thr = rate_conf_dict['threshold']
    if type(rate_enabled)==bool: 
        if rate_enabled:
            if type(rate_thr)==int and rate_thr>0:
                log_analysis.rate_analysis(rate_threshold=rate_thr)
            else:
                exit_and_fail("Rate threshold parameter should be a positive, non-zero integer")
    else:
        exit_and_fail("Rate enabled parameter should be of type boolean")

    msg_conf_dict = anal_conf['message']
    msg_enabled = msg_conf_dict['enabled']
    msg_length_thr = msg_conf_dict['threshold']['length']
    msg_repeatimes_thr = msg_conf_dict['threshold']['repetition']
    if type(msg_enabled)==bool: 
        if msg_enabled:
            if type(msg_length_thr)==int and msg_length_thr>0:
                if type(msg_repeatimes_thr)==int and msg_repeatimes_thr>0:
                    log_analysis.message_analysis(msg_length_thr, msg_repeatimes_thr)
                else:
                    exit_and_fail("Message repetition threshold parameter should be a positive, non-zero integer")
            else:
                exit_and_fail("Message length threshold parameter should be a positive, non-zero integer")
    else:
        exit_and_fail("Message enabled parameter should be of type boolean")

    severity_conf_dict = anal_conf['severity']
    if type(severity_conf_dict['enabled'])==bool: 
        if severity_conf_dict['enabled']:
            log_analysis.severity_analysis()
    else:
        exit_and_fail("Validation enabled parameter should be of type boolean")

    log_analysis.add_violation_excel_sheets(rate_thr, msg_repeatimes_thr)



if __name__ == "__main__":
    main()
