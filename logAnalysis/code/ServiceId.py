class ServiceId:

    def __init__(self, name=None, pod=None, container=None):
        self.name = name
        self.pods = []
        self.containers = []
        if pod != None and pod not in self.pods:
            self.pods.append(pod)
        if container != None and container not in self.containers:
            self.containers.append(container)

    def update_pods(self, pod=None):
        if pod != None and pod not in self.pods:
            self.pods.append(pod)

    def update_containers(self, container=None):
        if container != None and container not in self.containers:
            self.containers.append(container)