import os
import re
import zipfile
import sys
import json
class JD:
    def __init__(self, jd_path):
        sys.stderr.write(jd_path + '\n')
        self.jd_path = jd_path

    def getDownloadLinks(self):
        cfgPath = os.path.join(self.jd_path, 'cfg')
        zipFiles = {}
        #Find the zip files containing the download list
        for file in os.listdir(cfgPath):
            #why doesn't .zip$ work here?
            if match := re.fullmatch(r"downloadList(\d+)\.zip$", file):
                zipFiles[int(match.group(1))] = file

        if not zipFiles:
            sys.stderr.write("Couldn't find latest downloadZip in " + cfgPath)
            sys.exit(-1)

        #JDownloader writes each save in place, so the newest file can be incomplete for
        #several seconds. Fall back to an earlier save, which can itself be deleted at any time.
        error = None
        for ordinal in sorted(zipFiles, reverse=True):
            try:
                return self.readDownloadList(os.path.join(cfgPath, zipFiles[ordinal]))
            except (zipfile.BadZipFile, FileNotFoundError) as e:
                sys.stderr.write("Skipping " + zipFiles[ordinal] + ": " + str(e) + "\n")
                error = e
        raise error

    def readDownloadList(self, zipPath):
        with zipfile.ZipFile(zipPath, mode='r') as linkZip:
            ret = {}
            for entry in linkZip.namelist():
                #If this is a package.  We can skip these
                if match := re.match(r"^(\d+)$", entry):
                    continue
                #This is a link
                if match := re.match(r"^(\d+)_(\d+)$", entry):
                    linkData = json.loads(linkZip.read(entry))
                    #Skip disabled links
                    if not linkData.get('enabled'):
                        continue
                    url = linkData.get('url')
                    status = linkData.get('finalLinkState')
                    size = linkData.get('size')
                    ret[str(url)] = { 'size': int(size), 'status': status }

            return ret




if __name__ == '__main__':
    #Test case
    jd = JD(os.path.join(os.environ["HOME"],  'docker/jdownloader/config'))
    print(jd.getDownloadLinks())
