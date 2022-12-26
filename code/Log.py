import copy
from datetime import datetime
from common_functions import convert_json_to_dict

class Log:

    def __init__(self, log_data):
        self.version = None
        self.timestamp = None
        self.service_id = None
        self.severity = None
        self.message = None
        if type(log_data) == str:
            log = convert_json_to_dict(log_data)
        elif type(log_data) == dict:
            log = log_data
        if type(log) == str:
            self.message = log[:len(log)-2] # because log's format is "bla-bla-bla\n"
        else: # type(log)==dict                 
            if "version" in log.keys(): self.version = log['version']
            if "service_id" in log.keys(): self.service_id = log['service_id']
            if "severity" in log.keys(): self.severity = log['severity']
            if "message" in log.keys(): self.message = log['message']
            if "timestamp" in log.keys(): self.timestamp = self.formulate_timestamp(log['timestamp'])


    def formulate_timestamp(self, timestamp):
        '''
        Transforms the provide log timestamp from the given value to a python datetime object.
        This procedure can be successfully completed only if the timestamp is a string of the 
        form e.g. "2022-11-14T08:33:43.288686+00:00" or "2022-11-14T08:33:43.288686+0000". If 
        the provided timestamp is not a string or it is a string that cannot be converted to 
        a datetime object, it is considered invalid. 
        
        The chosen datetime format is: "%Y-%m-%dT%H:%M:%S.%fZ"
        e.g. "2022-11-14T08:33:43.288686+00:00" -->  "2022-11-14T08:33:43.288Z"
        Note: Using python's datetime object for the timestamp field we can easily perform date 
        and time operations concurrently. 
        '''
        if type(timestamp) != str:
            return timestamp
        try:
            td = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            td = timestamp
        return td


    def is_timestamp_valid(self) -> bool:
        if (self.timestamp != None) and (type(self.timestamp)==datetime):
            return True
        return False

    def is_version_valid(self) -> bool:
        if (self.version != None) and (type(self.version) == str): 
            if self.version == "0.2.0" or self.version == "0.3.0" or self.version == "1.0.0" or self.version == "1.1.0" or self.version == "1.2.0":
                return True
        return False

    def is_severity_valid(self) -> bool:
        if (self.severity != None) and (type(self.severity) == str):
            if self.severity == "debug" or self.severity == "info" or self.severity == "warning"  or self.severity == "error" or self.severity == "critical":
                return True
        return False

    def is_serviceId_valid(self) -> bool:
        if (self.service_id != None) and (type(self.service_id) == str):
            return True
        return False

    def is_message_valid(self) -> bool:
        if (self.message != None) and (type(self.message) == str):
            return True
        return False
               
    def is_valid(self) -> bool:
        if self.is_version_valid() and self.is_serviceId_valid() and self.is_severity_valid() and self.is_timestamp_valid() and self.is_message_valid():
            return True
        return False
           

    def convert_to_dict(self) -> dict:
        '''
        Converts a Log object to a dictionary
        Note: timestamp is a datetime object, we have to convert it to a string so that it can be
        properly displayed when using json.dumps to write the dictionary to a file
        '''
        Log_dict = vars(copy.deepcopy(self)) # vars(obj) converts a class object to a dictionary
        if type(Log_dict['timestamp']) == datetime:
            Log_dict['timestamp'] = str(Log_dict['timestamp'].isoformat('T')) 
        return Log_dict


    def get_str_datetime(self) -> str:
        return str(self.timestamp.date()) + "T" + str(self.timestamp.time()).split('.')[0]