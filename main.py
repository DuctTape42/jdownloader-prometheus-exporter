import jd
from urllib.parse import urlparse
import os
import sys
from prometheus_client.core import REGISTRY, SummaryMetricFamily, CounterMetricFamily, GaugeMetricFamily
import prometheus_client
import time
import re


class JDownloaderCollector:
    def __init__(self, jdPath, prefix):
        self.jdPath = jdPath
        self.prefix = prefix

    def collect(self):
        jdClient = jd.JD(self.jdPath)
        links = jdClient.getDownloadLinks()

        perHostStats = {}
        for link in links.items():
            host = mapHost(urlparse(link[0]).netloc)
            size = link[1]['size']
            status = mapStatus(link[1]['status'])

            if not host in perHostStats:
                perHostStats[host] = {}
            if not status in perHostStats[host]:
                perHostStats[host][status] = { 'count': 0, 'size': 0 }

            perHostStats[host][status]['count'] += 1
            perHostStats[host][status]['size'] += size


        countMetric = CounterMetricFamily(f"{self.prefix}_count", f"Number of links", labels=["status", "host"])
        sizeMetric = GaugeMetricFamily(f"{self.prefix}_bytes", f"Number of links", labels=["status", "host"])
        metrics = [countMetric, sizeMetric]

        for host in perHostStats:
            for status in perHostStats[host]:
                count = perHostStats[host][status]['count']
                size = perHostStats[host][status]['size']

                countMetric.add_metric(value=count, labels=[status, host])
                sizeMetric.add_metric(value=size, labels=[status, host])

        return metrics


def main(jdPath, port, prefix):
    #remove the default collectors
    prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
    prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
    prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
    REGISTRY.register(JDownloaderCollector(jdPath, prefix))
    prometheus_client.start_http_server(port)
    print ("Listening on port " + str(port))
    while True:
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit(0)

def collectStats(jdPath):
    jdClient = jd.JD(os.getenv("JDOWNLOADER_PATH"))
    links = jdClient.getDownloadLinks()

    perHostStats = {}
    for link in links.items():
        host = mapHost(urlparse(link[0]).netloc)
        size = link[1]['size']
        status = mapStatus(link[1]['status'])

        if not host in perHostStats:
            perHostStats[host] = {}
        if not status in perHostStats[host]:
            perHostStats[host][status] = { 'count': 0, 'size': 0 }

        perHostStats[host][status]['count'] += 1
        perHostStats[host][status]['size'] += size

    for host in perHostStats:
        for status in perHostStats[host]:
            print(host + "\t" + status + "\t" + "count:" + str(perHostStats[host][status]['count']) + ", " + str(perHostStats[host][status]['size']))




#Probably don't include _ in the output.
def mapStatus(status):
    if status == None:
        return "Pending"
    elif status == "FINISHED":
        return "Finished"
    elif status == "FINISHED_MD5":
        return "Finished"
    elif status == "FINISHED_SHA1":
        return "Finished"
    elif status == "FINISHED_SHA256":
        return "Finished"
    elif status == "FINISHED_MIRROR":
        return "Finished"
    elif status == "FAILED_EXISTS":
        return "Failed"
    elif status == "OFFLINE":
        return "Failed"
    elif status == "PLUGIN_DEFECT":
        return "Failed"
    else:
        sys.stderr.write("Unknown status: " + status + "\n")
        sys.exit(-1)

def mapHost(host):
    host = host.lower()
    if host == "clicknupload.click" or host == "clicknupload.download":
        host = "clicknupload.club"
    if host == "mega.co.nz":
        host = "mega.nz"
    if host == "fboom.me":
        host = "fileboom.me"
    return host

def hostToMetricName(host):
    if host == '1fichier.com':
        return 'fichier'
    host = re.sub(r'^(?:www\.)?(\w+)\.\w+?$', r'\1', host)
    host = re.sub(r'\.', ':', host)
    return host


if __name__ == '__main__':
    jdPath = os.getenv("JDOWNLOADER_PATH")
    if not jdPath:
        sys.stderr.write("Please set JDOWNLOADER_PATH")
        sys.exit(-1)
    prefix = os.getenv("PREFIX", default = 'jdownloader')
    port = os.getenv("PORT", default = 8000)
    main(jdPath, port, prefix)
