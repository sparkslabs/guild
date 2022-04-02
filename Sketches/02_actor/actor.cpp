
#include <iostream>
#include <unistd.h>

#include <thread>
// #include <condition_variable>
// #include <mutex>
#include <chrono>

using namespace std::chrono_literals;

bool WAITFOREXIT = true;
bool NOWAITFOREXIT = false;

class Actor { // I know this is bad practice. This is a sketch remember?
public:
    std::thread m_Thread;
    bool m_let_me_finish;

protected:
    virtual void main() {
        for(int i=0; i<20; i++) {
            std::this_thread::sleep_for(350ms);
            std::cout << "              Actor::main " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }

public:
    Actor(): m_Thread(), m_let_me_finish(false) { };
    Actor(bool X): m_Thread(), m_let_me_finish(X) { };
    void run() {
        m_Thread = std::thread(&Actor::main, this);
        std::cout << "m_let_me_finish:" << m_let_me_finish << std::endl;
        if (!m_let_me_finish) {
            m_Thread.detach();
        }
    }
    ~Actor() {
        if (m_let_me_finish) {
            m_Thread.join(); // Probably want to do something different?
        }
    }
};

class Dramatic : public Actor {     // Example Actor
public:
    Dramatic(): Actor() { };        // Always initialise cleanly...
    Dramatic(bool X): Actor(X) { }; // Always initialise cleanly...
    void main() {
        for(int i=0; i<20; i++) {
            std::this_thread::sleep_for(95ms);
            std::cout << "             I am DRAMATIC " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }
};


int main(int argc, char *argv[]) {
    std::cout << "Hello" << std::endl;
    std::cout << "World" << std::endl;

    Actor simple1;
    Actor simple2(WAITFOREXIT);
//    Dramatic Sherlock(WAITFOREXIT);
//    Dramatic Sherlock(NOWAITFOREXIT);
    Dramatic Sherlock;

    simple1.run();
    simple2.run();
    Sherlock.run();

    for(int i=0; i<10; i++) {
        std::this_thread::sleep_for(100ms);
        std::cout << "                                          Display From MainThread "<< std::this_thread::get_id() <<" ?:" << i << std::endl;
    }
 
    std::cout<<"Exit of Main function"<<std::endl;

    return 0;
}
