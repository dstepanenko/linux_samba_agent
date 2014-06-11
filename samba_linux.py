import sys
from daemon import runner
import time
import lockfile

from pprint import pprint
import concurrent.futures

sys.path.append('/home/ubuntu/netapp/netapp-mcdasl/.out/lib/Linux/i686')
import libCloudStoragePy

#from parse import *

SAMBA_CONFIG = "/etc/samba/smb.conf" #samba config file
TARGET_FILE = "linux_samba.txt" #file where we're going to write all parsed data
DELAY = 30 #daemon's delay in seconds
FILE_NAME = "/home/ubuntu/linux_samba.txt"

mcdasl = libCloudStoragePy.MCDASLInterfaceLight()

class App():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/var/run/samba_linux_daemon.pid'
        self.pidfile_timeout = 5

    def parse(self):
        #items = []

        with open(SAMBA_CONFIG) as f, open(TARGET_FILE, "w") as g:
            lines = tuple(f)

            i = 0
            name = "global"
            properties = {}

            for line in lines:
                i += 1
                #g.write(line + "\n")
                #g.write(line.rstrip('\n') + "\n")
                params = line.rstrip('\n').split()

                if not params or params[0][:1] in [";", "#"]:
                    continue

                #print params

                #is some string contain new block, it looks like [<name>]
                if params[0][0] == "[":
                    #push data into db - name, str(properties)
                    if properties:
                        #items.append('("%s", "%s")' % (name, str(properties)))
                        g.write('("%s", "%s")\n' % (name, str(properties)))
                    #block names can also contain whitespaces, but they are irrelevant
                    name = " ".join(params)[1:-1]
                    properties = {}
                    continue

                #parameter value can also contain '=' sign, so in case if string
                #of config looks like "name=bla = bla", name = "name",
                #value = "bla = bla"

                params = line.split("=")

                if not params:
                    continue

                #whitespaces in the name of
                field = " ".join(params[0].split())
                value = "=".join(params[1:])
                properties[field] = value

            if properties:
                g.write('("%s", "%s")\n' % (name, str(properties)))

    def do_mcdasl_stuff(self):
        try:
            status = mcdasl._open( libCloudStoragePy.CT_AMAZON,
                    #"172.18.16.180",
                    "127.0.0.1",
                    35357,
                    0,
                    "admin:admin",
                    "2d33673cac0f456c",
                    "",
                    4,
                    2
            )
            if( status <> libCloudStoragePy.OperationStatus.OS_OK ):
                raise RuntimeError( "Failed to open MCDASL light: {}".format(status))

            status = mcdasl.createContainer("volTest1", "")
            if( status <> libCloudStoragePy.OperationStatus.OS_OK ):
                raise RuntimeError( "Failed to create container: {}".format(status))
            objName1 = libCloudStoragePy.ObjectName("volTest1", FILENAME)
            status = mcdasl.upload( objName1, "Some object data to upload")
            if( status <> libCloudStoragePy.OperationStatus.OS_OK ):
                raise RuntimeError( "Failed to upload : {}".format(status))

            res = mcdasl.download( objName1 )
            if( res.status == libCloudStoragePy.OperationStatus.OS_OK ):
                print "Retrieved: {}".format(res.content)
            else:
                print "Download failure : {}".format(res.status)

            mcdasl.close()
        except RuntimeError as re:
            pprint(re)
        except KeyboardInterrupt:
            print "\nuser exit request"

    def run(self):
        while True:
            self.parse()
            self.do_mcdasl_stuff()
            time.sleep(10)


def main():
    while True:
        parse()
        time.sleep(DELAY)

#with daemon.DaemonContext(
#        stdout = sys.stdout, stderr = sys.stderr,
#        working_directory='/home/ubuntu',
#        pidfile=lockfile.FileLock('/home/ubuntu/linux_samba.pid')
#    ):
#    main()

app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
