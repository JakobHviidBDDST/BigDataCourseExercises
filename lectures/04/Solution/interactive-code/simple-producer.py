import threading
from client import get_producer, DEFAULT_TOPIC, produce_msg


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def main():
    timer1 = RepeatTimer(1.0, produce_msg, [1, DEFAULT_TOPIC, get_producer()])
    timer2 = RepeatTimer(1.0, produce_msg, [2, DEFAULT_TOPIC, get_producer()])
    timer3 = RepeatTimer(1.0, produce_msg, [3, DEFAULT_TOPIC, get_producer()])
    timer4 = RepeatTimer(1.0, produce_msg, [4, DEFAULT_TOPIC, get_producer()])
    timer5 = RepeatTimer(1.0, produce_msg, [5, DEFAULT_TOPIC, get_producer()])
    timer6 = RepeatTimer(1.0, produce_msg, [6, DEFAULT_TOPIC, get_producer()])

    try:
        timer1.start()
        timer2.start()
        timer3.start()
        timer4.start()
        timer5.start()
        timer6.start()
        while True:
            pass

    except KeyboardInterrupt:
        pass
    finally:
        timer1.cancel()
        timer2.cancel()
        timer3.cancel()
        timer4.cancel()
        timer5.cancel()
        timer6.cancel()


if __name__ == "__main__":
    main()
