
#include <iostream>
#include <thread>
#include <deque>
#include <exception>
#include <mutex>
#include <chrono>
#include <unistd.h>
#include <chrono>

using namespace std::chrono_literals;

// #include  <condition_variable>

bool WAITFOREXIT = true;
bool NOWAITFOREXIT = false;

void sleepmilli(int millis) {
    usleep(millis*1000);
}



class EmptyQueue: public std::exception {
    virtual const char* what() const throw() {
        return "EmptyQueue";
    }
};

class EmptyQueueTimeout: public std::exception {
    virtual const char* what() const throw() {
        return "EmptyQueueTimeout";
    }
};

using namespace std::chrono_literals;

template <class T> 
class Queue {
    std::deque<T> m_queue;
    std::mutex m_mutex;
public:

    void put(T item) {
        m_mutex.lock();
        m_queue.push_back(item);
        m_mutex.unlock();
    }

    T get_nowait() {
        T result;
        m_mutex.lock();
        if (m_queue.empty()) {
            m_mutex.unlock();
            throw EmptyQueue();
        }
        result = m_queue.front();
        m_queue.pop_front();
        m_mutex.unlock();
        return result;
    }

    T get() {
        return get_timeout(0);
    }

    T get_timeout(int timeout_ms) {
        int so_far_ms = 0;
        T result;
        while (true) {
            m_mutex.lock();
            if (!m_queue.empty()) {
                break;
            }
            m_mutex.unlock();
            std::this_thread::sleep_for(2ms);
            so_far_ms += 2;
            if (timeout_ms and so_far_ms > timeout_ms) {
                throw EmptyQueueTimeout();
            }
            std::this_thread::yield(); // be nice to other threads
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
            std::this_thread::sleep_for(350ms);
            std::cout << "              Actor::main " << std::this_thread::get_id() << " Executing:" << i << std::endl;
        }
    }

public:
    Actor(): m_Thread(), m_let_me_finish(false) { };
    Actor(bool X): m_Thread(), m_let_me_finish(X) { };
    void run() {
        m_Thread = std::thread(&Actor::main, this);
        if (!m_let_me_finish) {
            m_Thread.detach();
        }
    }
    ~Actor() {
        if (m_let_me_finish) {
            m_Thread.join(); // Appropriate?
        }
    }
};



class Producer : public Actor {
public:
    std::string m_tag;
    Queue<int> * q;

    Producer(std::string name): Actor(), m_tag(name) {}
    Producer(std::string name, Queue<int> * Q): Actor(), m_tag(name), q(Q) {}
    void set_outbox(Queue<int> * Q) {
        q = Q;
    }
    void main() {
        for(int i=0; i<20; i++) {
            std::this_thread::sleep_for(95ms);
            q->put(i);
        }
        q->put(-1);
    }
};


class Consumer : public Actor {
public:
    std::string m_tag;
    Queue<int> * q;

    Consumer(std::string name): Actor(), m_tag(name) {}
    Consumer(std::string name, Queue<int> * Q): Actor(), m_tag(name), q(Q) {}
    void set_inbox(Queue<int> * Q) {
        q = Q;
    }
    void main() {
        while(true) {
            int result;
            std::this_thread::sleep_for(105ms);
            try {
                result = q->get_timeout(10);
            } catch (EmptyQueueTimeout& e) {
                break;
            }
            std::cout << "CONSUMER " << m_tag << " " << result << std::endl;
        }
        std::cout << "CONSUMER " << m_tag << " exitting" << std::endl;
    }
};


int main(int argc, char *argv[]) {
    Queue<int> q;

    Producer P1("P1", &q);
    Producer P2("P2");
    Consumer C1("C1", &q);
    P2.set_outbox(&q);

    P1.run();
    P2.run();
    C1.run();

    for(int i=0; i<10; i++) {
            std::this_thread::sleep_for(200ms);
    }

    std::cout<<"Exit of Main function"<<std::endl;

    return 0;
}
