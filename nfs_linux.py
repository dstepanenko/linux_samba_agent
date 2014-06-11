import sys
from daemon import runner
import time
import lockfile
from parse import *

from pprint import pprint
import concurrent.futures

#directory where libCloudStoragePy.so is placed
sys.path.append('/home/stack/netapp-mcdasl/.out/lib/Linux/x86_64/')
import libCloudStoragePy


NFS_CONFIG = "/var/lib/nfs/etab"
TARGET_FILE = "linux_nfs.txt" #file where we're going to write all parsed data
DELAY = 30 #daemon's delay in seconds
FILE_NAME = "linux_nfs.txt"

mcdasl = libCloudStoragePy.MCDASLInterfaceLight()

class App():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/var/run/nfs_linux_daemon.pid'
        self.pidfile_timeout = 5

    def parse(self):
        items = []
        with open(NFS_CONFIG) as f, open(TARGET_FILE, "w") as g:
            lines = tuple(f)

            i = 0
            for line in lines:
                i += 1
                params = line.split()

                if not params:
                    continue

                folder = params[0]

                try:
                    pattern = "{}/{}({})"
                    r = parse(pattern, params[1])
                    (ip, netmask, flags) = r.fixed
                except Exception as exc:
                    try:
                        pattern = "{}({})"
                        r = parse(pattern, params[1])
                        (ip, flags) = r.fixed
                        netmask = '255.255.255.255'
                    except Exception as exc2:
                        print "Unable to parse %d line of nfs config" % i
                        raise Exception(exc2.message)
                #print ip, netmask, flags
                g.write("('%s', '%s', '%s', '%s')\n" % (folder, ip, netmask, flags))

    def do_mcdasl_stuff(self):
        try:
            status = mcdasl._open( libCloudStoragePy.CT_AMAZON,
                    #"172.18.16.180",
                    "s3.amazonaws.com",
                    #35357,
                    80,
                    0,
                    "AKIAJUUSO63UI7YUAIBA",
                    #"admin:admin",
                    "btI6dn8Q3ipM53/G8N+5LG/CxlqFrxWuZkppZL7t",
                    #"2d33673cac0f456c",
                    "",
                    4,
                    2
            )
            if( status <> libCloudStoragePy.OperationStatus.OS_OK ):
                raise RuntimeError( "Failed to open MCDASL light: {}".format(status))

            status = mcdasl.createContainer("volTest1", "")
            if( status <> libCloudStoragePy.OperationStatus.OS_OK ):
                raise RuntimeError( "Failed to create container: {}".format(status))
            objName1 = libCloudStoragePy.ObjectName("volTest1", TARGET_FILE)
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


app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
