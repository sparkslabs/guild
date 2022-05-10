#include <iostream>
#include <queue>
#include <string>

// Each exposed method gets a tag
enum __Simple_tags {
   HELLO,
   PHRASE,
};

// Base class to allow  single inbound queue (which effectively serialises requests)
struct arg_type { };

// Matches the parameter signature of __Simple::hello
struct __Simple_hello_arg_type : arg_type {
   int x;
   int y;
};

// Matches the parameter signature of __Simple::phrase
struct __Simple_phrase_arg_type : arg_type {
   std::string verb;
   std::string noun;
};

// Could be created and named on a per class basis
struct __Simple_MethodCall {
    __Simple_tags tag;
    arg_type* args;
};


class __Simple {
public:
    std::queue<__Simple_MethodCall> workqueue;  // Inbound calls come in here

    __Simple() { }
    void hello(int x, int y) {
        std::cout << "__Simple::hello" << " " << x << " " << y << "\n";
    }
    void phrase(std::string verb, std::string noun) {
        std::cout << "__Simple::phrase" << " " << verb << " " << noun << "\n";
    }

    void dispatch() {
        if (! workqueue.empty()) {
           __Simple_MethodCall call;
           call = workqueue.front();
           workqueue.pop();

           arg_type* raw_args = call.args;

           if (call.tag == HELLO) {
               std::cout << "TAG" << call.tag << "\n";
               __Simple_hello_arg_type *args;
               args =  (__Simple_hello_arg_type*) raw_args;
               hello(args->x, args->y);
           }
           if (call.tag == PHRASE) {
               std::cout << "TAG" << call.tag << "\n";
               __Simple_phrase_arg_type *args;
               args =  (__Simple_phrase_arg_type*) raw_args;
               phrase(args->verb, args->noun);
           }
        }
    }
};


class Simple {
private:
    __Simple s;
public:
    Simple() { }
    void hello(int x, int y) {
        std::cout << "SimpleFRONT" << " " << x << " " << y << "\n";
        __Simple_hello_arg_type args = { {}, x, y};
        __Simple_MethodCall call = {HELLO, &args};

        s.workqueue.push(call);
        s.dispatch();
    }
    void phrase(std::string verb, std::string noun) {
        std::cout << "SimpleFRONT" << " " << verb << " " << noun << "\n";
        __Simple_phrase_arg_type args = { {}, verb, noun };
        __Simple_MethodCall call = { PHRASE, &args};
        s.workqueue.push(call);
        s.dispatch();
    }
};


int main(int argc, char **argv) {
    Simple x;

    x.hello(5,10);
    x.phrase("hello", "world");

    return 0;
}
