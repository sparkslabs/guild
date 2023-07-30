#!/usr/bin/python

import sys

def slurp(filename):
    f = open(filename)
    raw = f.read()
    f.close()
    return raw

def makeActor(actorName):
    global actors
    assert actorName not in actors
    actors[actorName] = {
            "name" : actorName,
            "actormethods" : [],
        }

def mkActorMethod( actorName, fname, return_type, paramlist):
    global actors
    assert actorName in actors
    params = [ x.strip() for x in paramlist.split(",") ]
    if params == [""]:
        params = []
    nparams = []
    for param in params:
        p = param.rfind(" ")
        ptype, pname = param[:p].strip(), param[p:].strip()
        nparams.append({
                "name" : pname,
                "type" : ptype
            }
            )
    method = {
            "name" : fname,
            "paramlist" : nparams,
            "return_type" : return_type
        }
    actors[actorName]["actormethods"].append(method)


if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename")
    print("Need filename")
    sys.exit(1)

filename = sys.argv[1]

print()
print("Parsing", filename)
raw = slurp(filename)
lines = raw.split("\n")
#print(lines)

line = lines.pop(0)
l = 1
inactor = False
actorName = None
intestactor = False
testActorName = None
testActor = ""

actors = {}


while lines:
    if "ACTORMETHOD" in line:
        # print(l, "AM\t", line)
        if not inactor:
            print("WARNING: actormethod not in actor:", line)
        s = signature = line[:line.rfind("{")].strip()
        return_type = s[:s.find(" ")]
        rest = s[s.find(" "):].strip()
        assert rest[-1] == ")"
        fname = rest[:rest.find("(")]
        paramlist = rest[rest.find("(")+1:-1]
        mkActorMethod( actorName, fname, return_type, paramlist)

    elif "ACTOR" in line:
        # print(l, "ACT\t", line)
        inactor = True
        parts = line.split()
        assert parts[0] == "class"
        actorName = parts[1]
        makeActor(actorName)

    elif "Actor" in line and line.startswith("class"):
        testActor = line
        intestactor = True
    elif intestactor:
        testActor += "\n" + line
        if line.startswith("};"):
            intestactor = False

    elif inactor and line.startswith("};"):
        inactor = False

    else:
        pass

    line = lines.pop(0)
    l += 1

import pprint
print()
print("ACTORS:")
pprint.pprint(actors)
print()




for actorname in actors:
    actor = actors[actorname]
    actormethods = actor["actormethods"]
    print("class", actorname+"Actor", "{" )
    print("public:")
    for method in actormethods:
        return_type = method["return_type"]
        name = method["name"]
        params = method["paramlist"]
        nparams = []
        for param in params:
            nparams.append(param["type"] +" "+ param["name"])
        print("    " + return_type, name + "(" +", ".join(nparams)+ ") {")
        print('        std::cout << "'+actorname+'Actor::'+name+'"', end="")
        for param in params:
            print(' << ' + param["name"], end="")
            print(' << " "', end="")
        print(' <<"\\n";')
        print("    }")
    print("};")

# print(testActor)
