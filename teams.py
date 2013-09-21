#!/usr/bin/python
import sys
import getopt
import re
import os.path

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


class Contexts():
    def load_from_dir(self, teams_dir):
        self.contexts = []

        from os import listdir
        dats = [ os.path.join(teams_dir, f) for f in listdir(teams_dir)] 

        for dat in dats:
            context = Context()
            context.load_from_file(dat)
            self.contexts.append(context)

    def list_all(self):
        for context in self.contexts:
            print "%s => %s " % (context.countries,  context.name)



def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help", "list-all"])
        except getopt.error, msg:
             raise Usage(msg)


        contexts = Contexts()
        contexts.load_from_dir(teams_dir)
        
        for o, a in opts:
            print "analizzo %s" % o
            if o in ("-h", "--help"):
                raise Usage("help")
            elif o == "--list-all":
                contexts.list_all()
                return 0



    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
