ARG BOB_PYTHON3BUILDER_TAG
FROM armdocker.rnd.ericsson.se/proj-adp-cicd-drop/bob-python3builder:$BOB_PYTHON3BUILDER_TAG

RUN mkdir -p /logAnalysis &&\
    chmod -R g=u /logAnalysis

COPY .logChecker /logAnalysis/.logChecker
COPY code /logAnalysis/code

#Install python 3.10
RUN zypper addrepo https://download.opensuse.org/repositories/home:Simmphonie:python310:base/15.4/home:Simmphonie:python310:base.repo
RUN zypper --gpg-auto-import-keys refresh
RUN zypper -n install python310

#Install python3-pip
RUN zypper addrepo https://download.opensuse.org/repositories/home:Simmphonie:python310/15.4/home:Simmphonie:python310.repo
RUN zypper --gpg-auto-import-keys refresh
RUN zypper -n install python310-pip
RUN ls -la logAnalysis/
RUN pip3 install -r /logAnalysis/code/requirements.txt

#Create symbolink links and link libraries
RUN chmod +x /logAnalysis/code/main.py
RUN ln -sf /logAnalysis/code/main.py /usr/bin/logChecker

CMD ["/bin/sh"]