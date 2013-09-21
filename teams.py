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
    def show(self):
        print "%s => %s " % (self.countries,  self.name)

    def serialize(self):
        print "[TEAM]=\"%s\"" % self.name
        print "[COUNTRIES]=\"%s\"" % " ".join(self.countries)


class Contexts():
    def load_from_dir(self, teams_dir):
        self.contexts = {}

        from os import listdir
        dats = [ os.path.join(teams_dir, f) for f in listdir(teams_dir)] 

        for dat in dats:
            context = Context()
            context.load_from_file(dat)
            self.contexts[context.name] = context

    def serialize(self, context):
        self.contexts[context].serialize()


    def show(self, context):
        self.contexts[context].show()


    def show_all(self):
        for name, context in self.contexts.items():
            context.show()

    def who_owns(self, country):
        for name, context in self.contexts.items():
            if country in context.countries:
                return context.name
        return None



def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help", "show-all", "show-context=", "serialize-context=", "who-owns="])
        except getopt.error, msg:
             raise Usage(msg)


        contexts = Contexts()
        contexts.load_from_dir(teams_dir)
        
        for o, a in opts:
            if o in ("-h", "--help"):
                raise Usage("help")
            elif o == "--show-all":
                contexts.show_all()
                return 0
            elif o == "--show-context":
                context_name = a
                contexts.show(context_name)
                return 0
            elif o == "--serialize-context":
                context_name = a
                contexts.serialize(context_name)
                return 0
            elif o == "--who-owns":
                country = a
                print contexts.who_owns(country)
                return 0

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
