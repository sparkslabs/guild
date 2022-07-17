#include <iostream>
#include <queue>
#include <string>

// Note: While this shows the pattern, lifetimes of values are likely to be an issue when this is threaded.
// Needs confirming

namespace _Simple {

    // Each exposed method gets a tag
    enum function_tags {
        HELLO,
        PHRASE,
    };


    // Base class to allow  single inbound queue (which effectively serialises requests)
    struct arg_type {
        arg_type() = default;
    };

    // Matches the parameter signature of __Simple::hello
    struct hello_args : arg_type {
        int x;
        int y;
        hello_args(int a, int b) : x(a), y(b){}
        ~hello_args() {
            std::cout << "hello(" << x << ", " << y << "):" << long(this) <<" -- leaving scope\n";
        }
    };

    // Matches the parameter signature of __Simple::phrase
    struct phrase_args: arg_type {
        std::string verb;
        std::string noun;
        phrase_args(std::string a, std::string b) : verb(a), noun(b){}
        ~phrase_args() {
            std::cout << "phrase_args(" << verb << ", " << noun << ":" << long(this) <<" -- leaving scope\n";
        }
    };

    struct MethodCall {
        function_tags tag;
        arg_type* args;
    };

    // This is the "original" class. Note that it is essentially unchanged.
    class Simple {
    public:
        Simple() { }
        void hello(int x, int y) {
            std::cout << "_Simple::Simple::hello" << " " << x << " " << y << "\n";
        }
        void phrase(std::string verb, std::string noun) {
            std::cout << "_Simple::Simple::phrase" << " " << verb << " " << noun << "\n";
        }

    };

    class Wrapper {
    private:
        Simple s;
    public:

        Wrapper() { }

        std::queue<MethodCall> workqueue;  // Inbound calls come in here

        void push(MethodCall m) {
            workqueue.push(m);
        }
        
        void dispatch() {
            if (! workqueue.empty()) {
                MethodCall call;
                call = workqueue.front();
                workqueue.pop();

                arg_type* raw_args = call.args;

                if (call.tag == HELLO) {
                    std::cout << "TAG" << call.tag << "\n";
                    hello_args *args;
                    args =  (hello_args*) raw_args;
                    s.hello(args->x, args->y);
                }
                if (call.tag == PHRASE) {
                    std::cout << "TAG" << call.tag << "\n";
                    phrase_args *args;
                    args =  (phrase_args*) raw_args;
                    s.phrase(args->verb, args->noun);
                }
            }
        }
    };
}


class Simple {
private:
    _Simple::Wrapper s;
public:
    Simple() { }
    void hello(int x, int y) {
        std::cout << "SimpleFRONT" << " " << x << " " << y << "\n";
        _Simple::hello_args args = { x, y };
        _Simple::MethodCall call = {_Simple::HELLO, &args};

        s.push(call);
        s.dispatch();

    }
    void phrase(std::string verb, std::string noun) {
        std::cout << "SimpleFRONT" << " " << verb << " " << noun << "\n";
        _Simple::phrase_args args = { verb, noun };
        _Simple::MethodCall call = { _Simple::PHRASE, &args};
        s.push(call);
        s.dispatch();
        std::cout << __LINE__ << "\n";
    }
};



int main(int argc, char **argv) {
    Simple x;

    x.hello(5,10);
    x.phrase("hello", "world");

    return 0;
}
