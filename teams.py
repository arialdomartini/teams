#!/usr/bin/python
import sys
import getopt
import re
import os.path


class RunException(Exception):
    def __init__(self, msg):
        self.msg = msg

class Usage(Exception):
    def __init__(self, msg):
        helpmsg = """
Available commands:
  show --country=<country>
  show --context=<context>
  show-all
  assign --country=<country> --context=<context>
  who-owns --country=<country>
  serialize --context=<context>
  contexts
        """

        self.msg = "%s\n%s" %(msg, helpmsg)

teams_dir = "./dir-teams"


class Context():

    def load_from_file(self, file_path):
        self.file_path = file_path
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
        s= '[TEAM]="%s"\n' % self.name
        s=s+ '[COUNTRIES]="%s"' % " ".join(self.countries)
        return s


    def persist(self):
        content = self.serialize()
        with open(self.file_path, "w") as f:
            f.writelines(content)


    def assign(self, country):
        if country in self.countries:
            raise RunException('Country "%s" is already assigned to context "%s"' % (country, self.name))
        else:
            self.countries.append(country)


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
        return self.contexts[context].serialize()


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


    def assign(self, country, context_name):
        owner = self.who_owns(country)
        if owner:
            raise RunException('The country "%s" is already assigned to the context "%s"' % (country, owner))

        if not self.has(context_name):
            self.contexts[context_name] = self.create_context(context_name)

        
        print "Assigning the country %s to context %s" % (country, context_name)
        context = self.contexts[context_name]
        context.assign(country)
        context.persist()


    def has(self, context_name):
        return (context_name in self.contexts.keys())


    def create_context(self, context_name):
        context = Context()
        context.name = context_name
        context.countries = []
        context.file_path = os.path.join(teams_dir, "%s.dat" %context_name)

        return context




    def list_contexts(self):
        for name in self.contexts.keys():
            print name

        


def main(argv=None):
    if argv is None:
        argv = sys.argv
    argv.pop(0)

    if len(argv)==0:
        raise Usage("")

    commands = ["show", "show-all", "assign", "who-owns", "serialize", "contexts"] 
    
    
    try:
        
        if argv[0][0] != "-":
            if argv[0] in commands:
                command=argv.pop(0)
            else:
                raise Usage("%s is not a valid command" % argv[0])
    

        try:
            opts, args = getopt.getopt(argv, "h", ["help", "show-all", "show-context=", "who-owns=", "assign", "country=", "context="])
        except getopt.error, msg:
             raise Usage(msg)

        contexts = Contexts()
        contexts.load_from_dir(teams_dir)
        
        for o, a in opts:
            if o in ("-h", "--help"):
                raise Usage("Usage")
            elif o == "--country":
                country = a
            elif o == "--context":
                context = a

        if command=="assign":
            if "context" in locals() and "country" in locals():
                contexts.assign(country, context)
            else:
                raise Usage("--country and --context are mandatory")
        elif command=="show-all":
            contexts.show_all()
        elif command=="contexts":
            contexts.list_contexts()
        elif command=="who-owns":
            print contexts.who_owns(country)
        elif command=="show":
            if "context" in locals():
                contexts.show(context)
            elif "country" in locals():
                contexts.show(contexts.who_owns(country))
            else:
                print "nulla"
        elif command=="serialize":
            print contexts.serialize(context)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2
    except RunException, err:
        red="\033[0;31m"
        reset="\033[0m"
        print >>sys.stderr, red + "Error: " + reset + err.msg + reset
        return 2


if __name__ == "__main__":
    sys.exit(main())
