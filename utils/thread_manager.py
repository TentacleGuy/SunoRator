from threading import Thread, Event
from queue import Queue
import logging

class ThreadManager:
    def __init__(self):
        self.threads = {}
        self.stop_events = {}
        self.log_queue = Queue()

    def start_thread(self, name, target, args=()):
        if name in self.threads and self.threads[name].is_alive():
            return False
            
        stop_event = Event()
        self.stop_events[name] = stop_event
        
        thread = Thread(
            target=target,
            args=(*args, stop_event, self.log_queue),
            name=name,
            daemon=True
        )
        
        self.threads[name] = thread
        thread.start()
        return True

    def stop_thread(self, name):
        if name in self.stop_events:
            self.stop_events[name].set()

    def get_active_threads(self):
        return {name: thread for name, thread in self.threads.items() 
                if thread.is_alive()}

thread_manager = ThreadManager()
