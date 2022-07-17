#!/usr/bin/python3


import CppHeaderParser

if 0:
    cppHeader = CppHeaderParser.CppHeader("SampleClass.h")

    for classname in cppHeader.classes.keys():
        print(classname)

if 0:
    import CppHeaderParser
    cppHeader = CppHeaderParser.CppHeader("SimpleClass.h")
    print(cppHeader.toJSON())  

import CppHeaderParser
cppHeader = CppHeaderParser.CppHeader("SampleClass.h")
# cppHeader = CppHeaderParser.CppHeader("SimpleActor.h")
print("---------------------------------------------------------------------")
print(cppHeader.toJSON())  
# print(cppHeader)  
