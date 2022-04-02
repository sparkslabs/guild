
#include <iostream>
#include <unistd.h>
#include <thread>


void sleepmilli(int millis) {
    usleep(millis*1000);
}


void thread_function() {
    for(int i=0; i<10; i++) {
        sleepmilli(700);
        std::cout << "thread function " << std::this_thread::get_id() << " Executing:" << i << std::endl;
    }
}

struct ThreadFunctionObject {
    void operator()() {
        for(int i=0; i<20; i++) {
            sleepmilli(350);
            std::cout << "              ThreadFunctionObject " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }
};

struct Actor {
    std::thread m_Thread;
    void main() {
        for(int i=0; i<20; i++) {
            sleepmilli(500);
            std::cout << "              Actor::main " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }
    void run() {
        m_Thread = std::thread(&Actor::main, this);
        m_Thread.detach();
    }
};



int main(int argc, char *argv[]) {
    std::cout << "Hello" << std::endl;
    std::cout << "World" << std::endl;

    std::thread threadObj1( thread_function);
    std::thread threadObj2( (ThreadFunctionObject()));

    Actor simple;
    simple.run();
    for(int i=0; i<10; i++) {
        sleepmilli(1000);
        std::cout << "                                          Display From MainThread "<< std::this_thread::get_id() <<" ?:" << i << std::endl;
    }
 
//    threadObj1.join();
//    threadObj2.join();
    threadObj1.detach();  // Allows the process to exit without waiting for the thread to join
    threadObj2.detach();  // Allows the process to exit without waiting for the thread to join

    std::cout<<"Exit of Main function"<<std::endl;

    return 0;
}
