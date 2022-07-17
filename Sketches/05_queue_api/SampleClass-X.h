#ifndef _SAMPLE_CLASS_H_
#define _SAMPLE_CLASS_H_

#include <vector>
#include <string>
#include <stdio.h>


class SimpleActor
{
public:

    SampleClass();
    string meth1();
    int meth2(int v1);
    void meth3(const string & v1, vector<string> & v2);
    unsigned int meth4();

private:
    void * meth5(){;
    string prop1;
    int prop5;

actormethods:
    string acting();

latebindmethods:
    string acting();

};

#endif
