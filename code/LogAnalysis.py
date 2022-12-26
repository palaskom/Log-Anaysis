from common_functions import *
from ContainerLogs import *
from ServiceId import *
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class LogAnalysis:

    def __init__(self, input_folder=None):
        info("Initializing containers' parameters...")
        if input_folder == None:
            exit_and_fail("A folder path must be provided to proceed")
        self.service_ids = [] # list of ServiceId objects
        self.containers_logs = [] # list of ContainerLogs objects
        self.logs_fetched = False
        self.folders_created = False

        container_files = []
        for file in get_files_from_folder(input_folder):
            if file.startswith("eric"): container_files.append(file)

        for logFile in container_files:
            container_info = analyze_file_name(logFile)
            current_file_name = container_info['file_name']
            current_service_name = container_info['service_name']
            current_pod_name = container_info['pod_name']
            current_container_name = container_info['container_name']
            ##================== Update self.service_ids ==================##
            service_id_exists = False
            for service_id in self.service_ids:
                if current_service_name == service_id.name:
                    service_id_exists = True
                    service_id.update_pods(current_pod_name)
                    service_id.update_containers(current_container_name)
                    break
            if not service_id_exists:
                current_service_id = ServiceId(current_service_name, current_pod_name, current_container_name)
                self.service_ids.append(current_service_id)
            ##================== Update self.containers_logs ==================##
            log_exists = False
            for container_logs in self.containers_logs:
                if (current_pod_name == container_logs.pod_name) and (current_container_name == container_logs.container_name): 
                    log_exists = True
                    container_logs.logFiles.append(logFile)
                    break
            if not log_exists:
                container_logs = ContainerLogs(current_service_name, current_pod_name, current_container_name, current_file_name)
                self.containers_logs.append(container_logs)

        info("All containers have been initialized!")



    def create_container_folders(self, output_folder) -> None:
        info("Creating each container's folder...")
        if output_folder == None: 
            exit_and_fail("No output folder was given to store the results")
        for service_id in self.service_ids:
            create_folder(output_folder, service_id.name)
            service_folder = output_folder + service_id.name + "/"
            for pod in service_id.pods:
                create_folder(service_folder, pod)
                pod_folder = service_folder + pod + "/"
                for container in service_id.containers:
                    create_folder(pod_folder, container)
        for container_logs in self.containers_logs:
            container_logs.resultsFolder = output_folder + container_logs.service_name + "/" + container_logs.pod_name + "/" + container_logs.container_name + "/"
        self.folders_created = True
        info("All container folders have been created!")



    def fetch_logs(self, input_folder=None) -> None:

        info(f"Fetching logs from '{input_folder}' ...")

        if input_folder == None:
            exit_and_fail("Cannot fetch logs. No input folder was provided")
        for container_logs in self.containers_logs:
            container_logs.fetch_logs(input_folder)
        self.logs_fetched = True
        for container_logs in self.containers_logs:
            write_logs_to_file(container_logs.resultsFolder, "ALL-LOGS.txt", container_logs.get_logs())

        info("All logs have been fetched!")

    

    def validation_analysis(self) -> str:

        info("Categorizing logs based on their validity...")

        if not self.logs_fetched: 
            exit_and_fail("The logs have not been fetched")
        if not self.folders_created:
            exit_and_fail("Container folders have not been created")
        for container_logs in self.containers_logs:
            if not container_logs.contains_logs(): continue
            validation_folder = "validation-analysis/"
            create_folder(container_logs.resultsFolder, validation_folder)
            current_folder = container_logs.resultsFolder + validation_folder
            valid_logs, multiline_logs, no_json_logs, missing_fields_logs = container_logs.separate_logs()
            write_logs_to_file(current_folder, "valid-logs.txt", valid_logs)
            write_logs_to_file(current_folder, "invalid-logs-multiline.txt", multiline_logs)
            write_logs_to_file(current_folder, "invalid-logs-no_json_format.txt", no_json_logs)
            write_logs_to_file(current_folder, "invalid-logs-invalid_mandatory_fields.txt", missing_fields_logs)
            logs_number = len(container_logs.get_logs())
            data = [len(valid_logs)/logs_number, len(multiline_logs)/logs_number, len(no_json_logs)/logs_number, len(missing_fields_logs)/logs_number]
            labels = ["valid", "multiline", "no-json-format", "       invalid\nmandatory-fields"]
            displayed_data, displayed_labels = [], []
            for i in range(0,len(data)):
                if data[i] >= 0.01: # do not display proportions <1% 
                    displayed_data.append(data[i])
                    displayed_labels.append(labels[i])
            plt.pie(displayed_data, labels=displayed_labels, autopct='%.0f%%')
            plt.suptitle("Logs categories according to their validation status", fontsize=14)
            container_period = container_logs.get_datetime_period()
            plt.title(f"period: {container_logs.get_datetime_period()}", fontsize=10)
            plt.savefig(current_folder + "pie-chart.png")
            plt.clf()

        info(f"All logs have been successfully separated according to their validity")


               
    def rate_analysis(self, store_logs_per_sec=False, rate_threshold=10):
        if not self.logs_fetched: 
            exit_and_fail("The logs have not been fetched")
        
        info("Starting log rate analysis...")

        rate_folder_name = "rate-analysis/"
        folder_logs_sec = "logs-per-second/"
        folder_logs_sec_thr = f"logs-above-{rate_threshold}-per-second/"
    
        for container_logs in self.containers_logs:
            if not container_logs.contains_logs(): continue
            create_folder(container_logs.resultsFolder, rate_folder_name)
            rate_folder = container_logs.resultsFolder + rate_folder_name
            if store_logs_per_sec: create_folder(rate_folder, folder_logs_sec)
            create_folder(rate_folder, folder_logs_sec_thr)

            container_period_timestamps, container_logs_periods = container_logs.get_logs_per_period()
            periods = len(container_logs_periods)
            
            numOf_logs_period = []
            for period in range(0, periods):
                numOf_logs_period.append(len(container_logs_periods[period]))
                if store_logs_per_sec: 
                    write_logs_to_file(rate_folder + folder_logs_sec, f"period-{period+1}.txt", container_logs_periods[period])
                if numOf_logs_period[period] >=rate_threshold: 
                    write_logs_to_file(rate_folder + folder_logs_sec_thr, f"period-{period+1}.txt", container_logs_periods[period])
                
            plt.plot(range(1,len(numOf_logs_period)+1), numOf_logs_period)
            plt.xlabel("period"), plt.ylabel("number of logs")
            plt.suptitle("Logs generated every second", fontsize=14)
            plt.title(f"period: {container_logs.get_datetime_period()}", fontsize=10)
            plt.savefig(rate_folder + "rate.png")
            plt.clf()                

            container_period_timestamps_str = [str(s) for s in container_period_timestamps]
            all_df = pd.DataFrame(
                {
                    'Start_Timestamp': container_period_timestamps_str[0:periods],
                    'End_Timestamp': container_period_timestamps_str[1:periods+1],
                    'Logs': numOf_logs_period
                },
                index = np.arange(1, periods+1)
            )
            all_df.index.name = 'Period'
            all_df.to_excel(container_logs.resultsFolder + 'results.xlsx', sheet_name="overview")
            container_logs.resultsExcel = pd.ExcelFile(container_logs.resultsFolder + 'results.xlsx')
                        


    def message_analysis(self, char_thr=250, repeat_times_thr=2):
        if not self.logs_fetched: 
            exit_and_fail("The logs have not been fetched")

        msg_folder_name = "message-analysis/"
        char_folder_name = f"messages-above-{char_thr}-characters/"
        repeat_folder_name = f"messages-repeated-at-least-{repeat_times_thr}-times-in-a-second/"

        for container_logs in self.containers_logs:
            if not container_logs.contains_logs(): continue
            create_folder(container_logs.resultsFolder, msg_folder_name)
            msg_folder = container_logs.resultsFolder + msg_folder_name
            create_folder(msg_folder, char_folder_name)
            create_folder(msg_folder, repeat_folder_name)

            container_period_timestamps, container_logs_periods = container_logs.get_logs_per_period()
            periods = len(container_logs_periods)

            long_msg_periods = [] 
            repeat_msg_periods = []
            for logs_period in container_logs_periods: # iterate over every period of 1sec
                long_msg_period = []
                repeat_msg_period = []
                msg_with_repeatimes = []
                for log in logs_period: # iterate over each log of the period
                    if len(log.message) >= char_thr:
                        long_msg_period.append(log)
                    for i in range(0,len(msg_with_repeatimes)):
                        if log.message == msg_with_repeatimes[i]['message']:
                            msg_with_repeatimes[i]['repeat times'] +=1
                            break
                    msg_with_repeatimes.append({'message': log.message, 'repeat times': 1})
                for msg_dict in msg_with_repeatimes:
                    if msg_dict['repeat times'] >= repeat_times_thr:
                        repeat_msg_period.append(msg_dict)
                long_msg_periods.append(long_msg_period)
                repeat_msg_periods.append(repeat_msg_period)

            for period in range(0, periods):
                if len(long_msg_periods[period]) >0:
                    write_logs_to_file(msg_folder + char_folder_name, f"period-{period+1}.txt", long_msg_periods[period])
                if len(repeat_msg_periods[period]) >0:
                    with open(msg_folder + repeat_folder_name + f"period-{period+1}.txt", 'w') as f:
                        f.write(json.dumps(repeat_msg_periods[period], indent=2) + "\n")

            numberOf_long_msg_periods = [len(s) for s in long_msg_periods]
            numberOf_repeat_msg_periods = [len(s) for s in repeat_msg_periods]

            results_xls = pd.ExcelFile(container_logs.resultsFolder + 'results.xlsx')
            all_df = pd.read_excel(results_xls, 'overview')
            all_df.set_index("Period", inplace=True)
            all_df["Long_Messages"] = numberOf_long_msg_periods
            all_df["Repeated_Messages"] = numberOf_repeat_msg_periods
            all_df.to_excel(container_logs.resultsFolder + 'results.xlsx', sheet_name="overview")
            container_logs.resultsExcel = pd.ExcelFile(container_logs.resultsFolder + 'results.xlsx')



    def severity_analysis(self):
        if not self.logs_fetched: 
            exit_and_fail("The logs have not been fetched")

        severity_folder_name = "severity-analysis/"
        error_folder_name = "error-messages/"

        for container_logs in self.containers_logs:

            if not container_logs.contains_logs(): continue
            create_folder(container_logs.resultsFolder, severity_folder_name)
            severity_folder = container_logs.resultsFolder + severity_folder_name
            create_folder(severity_folder, error_folder_name)

            container_period_timestamps, container_logs_periods = container_logs.get_logs_per_period()

            period = 1
            numberOf_error_logs_periods = []
            for logs_period in container_logs_periods:
                error_logs_period = []
                numberOf_error_logs_period = 0
                for log in logs_period:
                    if (log.severity == "error"): 
                        error_logs_period.append(log)
                        numberOf_error_logs_period +=1
                if len(error_logs_period) >0:
                    write_logs_to_file(severity_folder + error_folder_name, f"period-{period}.txt", error_logs_period)
                numberOf_error_logs_periods.append(numberOf_error_logs_period)
                period +=1

            sum_error = sum(item for item in numberOf_error_logs_periods)
            sum_info = 0
            sum_debug = 0
            sum_critical = 0
            sum_warning = 0
            sum_none_severity = 0
            logs = container_logs.get_logs()
            for log in logs:
                match log.severity:
                    case "info": sum_info +=1
                    case "debug": sum_debug +=1
                    case "critical": sum_critical +=1
                    case "warning": sum_warning +=1
                    case "None": sum_none_severity +=1

            sum_logs = len(logs)
            sum_per_sevLevel = [sum_info, sum_debug, sum_critical, sum_warning, sum_error, sum_none_severity]
            data = [x/sum_logs for x in sum_per_sevLevel]
            labels = ["info", "debug", "critical", "warning", "error", "undefined"]
            displayed_data, displayed_labels = [], []
            for i in range(0,len(data)):
                if data[i] >= 0.01: # do not display proportions <1%
                    displayed_data.append(data[i])
                    displayed_labels.append(labels[i])
            plt.pie(displayed_data, labels=displayed_labels, autopct='%.0f%%')
            plt.suptitle("Logs - Severity Statistics", fontsize=14)
            plt.title(f"period: {container_logs.get_datetime_period()}", fontsize=10)
            plt.savefig(severity_folder + "pie-chart.png")
            plt.clf()

            objects = ("info", "debug", "critical", "warning", "error", "undefined")
            y_pos = np.arange(len(objects))
            plt.bar(y_pos, sum_per_sevLevel, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            plt.ylabel('Number of logs')
            plt.title('Logs distribution based on severity levels')
            plt.savefig(severity_folder + "bar-chart.png")
            plt.clf()

            results_xls = pd.ExcelFile(container_logs.resultsFolder + 'results.xlsx') # all sheets
            all_df = pd.read_excel(results_xls, 'overview')
            all_df.set_index("Period", inplace=True)
            all_df["Error_Logs"] = numberOf_error_logs_periods
            all_df.to_excel(container_logs.resultsFolder + 'results.xlsx', sheet_name='overview')
            container_logs.resultsExcel = pd.ExcelFile(container_logs.resultsFolder + 'results.xlsx')

    

    def add_violation_excel_sheets(self, rate_threshold=10, repeat_times_thr=2):
        for container_logs in self.containers_logs:
            if not container_logs.contains_logs(): continue
            all_df = pd.read_excel(container_logs.resultsExcel, 'overview')
            all_df.set_index("Period", inplace=True)
            rate_violation_df = all_df[all_df["Logs"]>=rate_threshold]
            repeat_violation_df = all_df[all_df["Repeated_Messages"]>=repeat_times_thr]
            with pd.ExcelWriter(container_logs.resultsFolder + "results.xlsx") as writer:
                all_df.to_excel(writer, sheet_name="overview")  
                rate_violation_df.to_excel(writer, sheet_name="rate_violation")
                repeat_violation_df.to_excel(writer, sheet_name="msg_repeat_violation")
