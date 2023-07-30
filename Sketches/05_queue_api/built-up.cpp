#include <iostream>

class Simple {   // ACTOR
public:
    Simple() { }
    void noarg() { // ACTORMETHOD
        std::cout << "Simple::noarg" << "()" << "\n";
    }
    void onearg(std::string who) { // ACTORMETHOD
        std::cout << "Simple::onearg" << " " << who << "\n";
    }
    void hello(int x, int y) { // ACTORMETHOD
        std::cout << "Simple::hello" << " " << x << " " << y << "\n";
    }
    void phrase(std::string verb, std::string noun) {  // ACTORMETHOD
        std::cout << "Simple::phrase" << " " << verb << " " << noun << "\n";
    }

};

class SimpleActor {
public:
    void noarg() {
        std::cout << "SimpleActor::noarg" << "\n";
    }
    void onearg(std::string who) {
        std::cout << "SimpleActor::onearg" << " " << who << "\n";
    }
    void hello(int x, int y) {
        std::cout << "SimpleActor::hello" << " " << x << " " << y << "\n";

    }
    void phrase(std::string verb, std::string noun) {
        std::cout << "SimpleActor::phrase" << " " << verb << " " << noun << "\n";
    }
};




int main(int argc, char **argv) {
    Simple x;
    SimpleActor y;

    x.hello(5,10);
    x.phrase("hello", "world");

    y.hello(5,10);
    y.phrase("hello", "world");

    return 0;
}
