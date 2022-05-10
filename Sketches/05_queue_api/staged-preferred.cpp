#include <iostream>
#include <queue>
#include <string>

// This is what we want to write
// The result being something that looks like the code in staged.cpp
// In python this occurs dynamically via a metaclass - which takes a class
// and builds the actual class

// In C++ it's reasonable to assume that this would need to be a build step
// - that takes the class definition and builds the appropriate code

class Simple : Actor {
public:

    Simple() { }

actormethods:
    void hello(int x, int y) {
        std::cout << "Simple::hello" << " " << x << " " << y << "\n";
    }
    void phrase(std::string verb, std::string noun) {
        std::cout << "Simple::phrase" << " " << verb << " " << noun << "\n";
    }

// These are actually calls to actor methods, so we really could do this
latebind:
    void output(std::string x);
};


int main(int argc, char **argv) {
    Simple x;

    x.start();

    x.hello(5,10);
    x.phrase("hello", "world");

    x.join()

    return 0;
}
