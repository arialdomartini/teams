#!/usr/bin/python
import sys
import getopt
import re

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

teams_dir = "./dir-teams"


class Context():

    def load_from_file(self, file_path):
        with open(file_path) as f:
            lines = f.readlines() 
            if len(lines) != 2:
                raise Exception("bad file %s" % file_path)
            else:
                name = re.match("\[TEAM\]=\"(.*)\"", lines[0]).groups()[0]
                countries_string = re.match("\[COUNTRIES\]=\"(.*)\"", lines[1]).groups()[0]
                countries = countries_string.split(" ")

                self.name = name
                self.countries = countries





def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error, msg:
             raise Usage(msg)


        context = Context()
        context.load_from_file("%s/dwh.dat" % teams_dir)
        print context.name
        print context.countries



    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
