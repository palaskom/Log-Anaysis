from Log import *
from common_functions import *
from datetime import timedelta


class ContainerLogs:
    
    def __init__(self, service_name=None, pod_name=None, container_name=None, logFile=None):
        self.service_name = service_name
        self.pod_name = pod_name
        self.container_name = container_name
        self.previous_logs = [] # logs before restart -> list of Log objects
        self.next_logs = [] # logs after restart -> list of Log objects
        self.logFiles = []
        self.resultsFolder = None
        self.resultsExcel = None
        if logFile != None: self.logFiles.append(logFile)
            

    def fetch_logs(self, folder_path:str):
        if len(self.logFiles) == 0:
            warning(f"No logs were fetched for the '{self.container_name}' container of the '{self.pod_name}' pod")
        else:
            for logFile in self.logFiles:
                logs = read_logs_from_file(folder_path, logFile, "line")
                for log in logs:
                    log_obj = Log(log)
                    if "previous" in logFile:
                        self.previous_logs.append(log_obj)
                    else:
                        self.next_logs.append(log_obj)


    def get_logs(self):
        return self.previous_logs + self.next_logs


    def contains_logs(self) -> bool:
        if len(self.get_logs()) > 0:
            return True
        return False


    def separate_logs(self):
        valid_logs = []
        multiline_logs = []
        no_json_logs = []
        missing_fields_logs = []
        for log in self.get_logs():
            if log.is_valid(): 
                valid_logs.append(log)
            else:
                if log.is_message_valid() and (log.message.startswith('\tat') or log.message.startswith('io') or log.message.startswith('Caused by')):
                    multiline_logs.append(log)
                elif log.is_message_valid() and log.version==None and log.severity==None and log.service_id==None and log.timestamp==None:
                    no_json_logs.append(log)
                else:
                    missing_fields_logs.append(log)
        return valid_logs, multiline_logs, no_json_logs, missing_fields_logs


    def get_first_valid_timestamp_log(self):
        for log in self.get_logs():
            if log.is_timestamp_valid(): return log
        return None

    def get_last_valid_timestamp_log(self):
        for log in reversed(self.get_logs()):
            if log.is_timestamp_valid(): return log
        return None

    def get_datetime_period(self):
        logs_number = len(self.get_logs())
        if logs_number == 0:
            return None
        first_valid_timestamp_log = self.get_first_valid_timestamp_log()
        if first_valid_timestamp_log==None: return "no valid timestamps"
        last_valid_timestamp_log = self.get_last_valid_timestamp_log()
        return first_valid_timestamp_log.get_str_datetime() + " - " + last_valid_timestamp_log.get_str_datetime()


    def get_logs_per_period(self):
        period_timestamps = []
        last_valid_timestamp_log = self.get_last_valid_timestamp_log()
        if last_valid_timestamp_log==None:
            return ["None", "None"], [self.get_logs()]
        last_valid_td = last_valid_timestamp_log.timestamp
        first_valid_timestamp_log = self.get_first_valid_timestamp_log()
        current_td_sec = first_valid_timestamp_log.timestamp
        while True:
            if current_td_sec >= last_valid_td:
                period_timestamps.append(current_td_sec)
                break
            period_timestamps.append(current_td_sec)
            current_td_sec += timedelta(seconds=1)
        logs = self.get_logs()
        logs_periods = [[] for i in range(len(period_timestamps)-1)]
        period = 1
        index = 0
        while index < len(logs):
            if (not logs[index].is_timestamp_valid()) or (logs[index].timestamp <= period_timestamps[period]):
                (logs_periods[period-1]).append(logs[index])
                index +=1
            else:
                period +=1
        return period_timestamps, logs_periods