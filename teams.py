#!/usr/bin/python
import sys
import getopt
import re
import os.path

teams_dir = "/opt/tools/applicationdelivery/teams"
exclusion_file = "/opt/dist/conf/do_not_deploy_on_countries.conf"
selfname=sys.argv[0]

class RunException(Exception):
    def __init__(self, msg):
        self.msg = msg

class Usage(Exception):
    def __init__(self, msg):
        helpmsg = """
Usage:
%s <command> [--country=<country>] [--context=<context>]

Available commands:
  update-board
  show --country=<country>
  show --context=<context>
  show-all
  assign --country=<country> --context=<context>
  release --country=<country> --context=<context>
  who-owns --country=<country>
  serialize --context=<context>
  contexts
        """ % os.path.basename(selfname)
        self.msg = helpmsg
        if msg:
            self.msg = "%s\n%s" %(msg, helpmsg)


class Context():

    def load_from_file(self, file_path):
        self.file_path = file_path
        with open(file_path) as f:
            lines = f.readlines() 
            if len(lines) != 2:
                raise Exception("bad file %s" % file_path)
            else:
                name = re.match("TEAMNAME=\"(.*)\"", lines[0]).groups()[0]
                countries_string = re.match("TEAMCOUNTRIES=\"(.*)\"", lines[1]).groups()[0]
                countries = countries_string.split(" ")

                self.name = name
                self.countries = countries


    def show(self):
        print "%s => %s " % (self.name, self.countries)


    def serialize(self):
        s= 'TEAMNAME="%s"\n' % self.name
        s=s+ 'TEAMCOUNTRIES="%s"' % " ".join(self.countries)
        return s


    def persist(self):
        if len(self.countries) > 0:
            with open(self.file_path, "w") as f:
                content = self.serialize()
                f.writelines(content)
        else:
            os.remove(self.file_path)


    def assign(self, country):
        if country in self.countries:
            raise RunException('Country "%s" is already assigned to context "%s"' % (country, self.name))
        else:
            self.countries.append(country)

    def release(self, country):
        if country not in self.countries:
            raise RunException('Country "%s" is not assigned to context "%s"' % (country, self.name))
        else:
            self.countries.remove(country)
            self.update_board()

    def is_empty(self):
        return len(self.countries) == 0


class ExclusionList():

    def __init__(self):
        self.countries = []

    def load_from_file(self, file_path):
        self.file_path = file_path
        with open(file_path) as f:
            self.countries = [f.strip() for f in f.readlines() if len(f)>0]

    def start_excluding(self, country):
        if country in self.countries:
            raise RunException('Uhm. The country "%s" was already in the exclusion file. This shouldn\'t happen' % country)
        self.countries.append(country)

    def stop_excluding(self, country):
        if country not in self.countries:
            raise RunException('Uhm. The country "%s" was not in the exclusion file. This shouldn\'t happen' % country)
        self.countries.remove(country)


    def persist(self):
        with open(self.file_path, "w") as f:
            f.write("\n".join(self.countries))



class Contexts():
    def __init__(self, exclusion_list):
        self.exclusion_list = exclusion_list

    def load_from_dir(self, teams_dir):
        self.contexts = {}

        from os import listdir
        dats = [ os.path.join(teams_dir, f) for f in listdir(teams_dir) if f != ".svn"] 

        for dat in dats:
            context = Context()
            context.load_from_file(dat)
            self.contexts[context.name] = context

    def update_board(self):
        rows = []
        for name in sorted(self.contexts.keys()):
            row = "<tr><td>%s</td><td>%s</td></tr>" % (name, ", ".join(self.contexts[name].countries))
            rows.append(row)
        rows_html = " ".join(rows)

        html = """<html>
  <body>
   <head>
     <style TYPE="text/css">
        table {
          width:100%;
          font-size:150%;
          font-family: arial;
          border:0;
border-collapse: collapse;
        }
        thead tr { background:#fff; font-size:75%; border:0;}
        tbody tr:nth-child(even) {background:#fff; font-weight:bold;}
        tbody tr:nth-child(odd) {background: #eeeeee; font-weight:bold;}
        td { padding:0.2em; }
     </style>
   </head>
    <table>
      <thead>
        <tr>
          <td>Context</td>
          <td>Countries</td>
        </tr>
      </thead>
      <tbody>
        $$$
      </tbody>
    </table>
  </body>
</html>
"""
        html = html.replace("$$$", rows_html)
        with open("board.html", "w") as f:
            f.write(html)

    def serialize(self, context):
        return self.contexts[context].serialize()


    def show(self, context_name):
        if not self.has(context_name):
            raise RunException('There\'s no context named "%s"\nUse the "contexts" command to list all the available contexts' % context_name)
        self.contexts[context_name].show()


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
        self.save(context)
        self.exclusion_list.start_excluding(country)
        self.exclusion_list.persist()


    def release(self, country, context_name):
        owner = self.who_owns(country)
        if owner == None:
            raise RunException('The country "%s" is not assigned' % country)
        if owner != context_name:
            raise RunException('The country "%s" is assigned to the context "%s" and not to the context "%s"' % (country, owner, context_name))

        if not self.has(context_name):
            raise RunException('"The context "%s" does not exist' % context_name)

        
        context = self.contexts[context_name]
        context.release(country)
        self.save(context)
        self.exclusion_list.stop_excluding(country)
        self.exclusion_list.persist()
        self.update_board()



    def save(self, context):
        context.persist()
        if context.is_empty():
            del self.contexts[context.name]


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

    commands = ["show", "show-all", "assign", "release", "who-owns", "serialize", "contexts", "update-board"]

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

        exclusion_list = ExclusionList()
        exclusion_list.load_from_file(exclusion_file)

        contexts = Contexts(exclusion_list)
        contexts.load_from_dir(teams_dir)

        
        for o, a in opts:
            if o in ("-h", "--help"):
                raise Usage("")
            elif o == "--country":
                country = a
            elif o == "--context":
                context = a
        if command=="update-board":
            contexts.update_board()
        elif command=="assign":
            if "context" in locals() and "country" in locals():
                contexts.assign(country, context)
            else:
                raise Usage("--country and --context are mandatory")
        elif command=="release":
            if "context" in locals() and "country" in locals():
                contexts.release(country, context)
            else:
                raise Usage("--country and --context are mandatory")
        elif command=="show-all":
            contexts.show_all()
        elif command=="contexts":
            contexts.list_contexts()
        elif command=="who-owns":
            if "country" in locals():
                print contexts.who_owns(country)
            else:
                raise RunException("Please, specify a country using the --country option")

        elif command=="show":
            if "context" in locals():
                contexts.show(context)
            elif "country" in locals():
                contexts.show(contexts.who_owns(country))
            else:
                raise Usage("show requires either --country or --context")
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
