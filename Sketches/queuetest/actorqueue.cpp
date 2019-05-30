
#include <iostream>
#include <thread>
#include <deque>
#include <exception>
#include <mutex>

// #include <condition_variable>
// #include <mutex>


void busywait(int lmax) {
    for(int i=0; i<lmax; i++) {
        for(int j=0; j<lmax; j++) {
            for(int k=0; k<lmax; k++) {
            }
        }
    }
}

bool WAITFOREXIT = true;
bool NOWAITFOREXIT = false;

class StopIteration: public std::exception {
    virtual const char* what() const throw() {
        return "StopIteration";
    }
};


template <class T> 
class Queue {
private:
    std::deque<T> m_queue;
    std::mutex m_mutex;
public:
    void put(T item) {
        m_queue.push_back(item);
        std::cout << "APPEND " << item << std::endl;
    }
    T get() {  //        std::cout << "Really ought to check the queue length first" << std::endl;
        T result;
        m_mutex.lock();
        if (m_queue.empty()) {
            m_mutex.unlock();
            throw StopIteration();
        }
        result = m_queue.front();
        m_queue.pop_front();
        m_mutex.unlock();
        return result;
    }
};


class Actor { // I know this is bad practice. This is a sketch remember?
public:
    std::thread m_Thread;
    bool m_let_me_finish;

protected:
    virtual void main() {
        for(int i=0; i<20; i++) {
            busywait(350);
            std::cout << "              Actor::main " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }

public:
    Actor(): m_Thread(), m_let_me_finish(false) { };
    Actor(bool X): m_Thread(), m_let_me_finish(X) { };
    void run() {
        m_Thread = std::thread(&Actor::main, this);
        if (!m_let_me_finish) {
            std::cout << "m_let_me_finish:" << m_let_me_finish << std::endl;
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
            busywait(95);
            std::cout << "             I am DRAMATIC " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }
};

void actortest() {
    Actor simple1;
    Actor simple2(NOWAITFOREXIT);
//    Dramatic Sherlock(WAITFOREXIT);
//    Dramatic Sherlock(NOWAITFOREXIT);
    Dramatic Sherlock;

    simple1.run();
    simple2.run();
    Sherlock.run();

    for(int i=0; i<10; i++) {
        busywait(100);
        std::cout << "                                          Display From MainThread "<< std::this_thread::get_id() <<" ?:" << i << std::endl;
    }
}

int main(int argc, char *argv[]) {
    Queue<int> q;

    std::cout << "Hello" << std::endl;
    std::cout << "World" << std::endl;

    for(int i=0; i<10; i++) {
        q.put(i);
    }
    while(true) {
        try {
            std::cout << "POP: " << q.get() << std::endl;
        } catch (StopIteration& e) {
            break;
        }
    }

    // actortest(); 
    std::cout<<"Exit of Main function"<<std::endl;

    return 0;
}
