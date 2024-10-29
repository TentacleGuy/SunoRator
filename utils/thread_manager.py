from threading import Thread, Event
from queue import Queue
import logging
from utils.socket_manager import socketio
import time

class ThreadManager:
    def __init__(self):
        self.threads = {}
        self.stop_events = {}
        self.pause_events = {}
        self.log_queue = Queue()

    def start_thread(self, name, target, args=()):
        if name in self.threads and self.threads[name].is_alive():
            return False
            
        stop_event = Event()
        pause_event = Event()
        self.stop_events[name] = stop_event
        self.pause_events[name] = pause_event
        
        thread = Thread(
            target=target,
            args=(*args, stop_event, self.log_queue, pause_event),  # Add pause_event here
            name=name,
            daemon=True
    )
        
        self.threads[name] = thread
        thread.start()
        socketio.emit('thread_started')
        return True

    def _wrapped_target(self, name, target, args, stop_event, pause_event):
        try:
            while not stop_event.is_set():
                if pause_event.is_set():
                    time.sleep(0.1)  # Add small delay while paused
                    continue
                target(*args, stop_event, self.log_queue)
                break
        finally:
            if name in self.threads:
                del self.threads[name]
                del self.stop_events[name]
                del self.pause_events[name]

    def stop_thread(self, name):
        if name in self.stop_events:
            self.stop_events[name].set()
            # Immediate cleanup
            if name in self.threads:
                del self.threads[name]
            if name in self.stop_events:
                del self.stop_events[name]
            if name in self.pause_events:
                del self.pause_events[name]
            socketio.emit('thread_stopped', {'name': name})

    def pause_thread(self, name):
        if name in self.pause_events:
            self.pause_events[name].set()
            socketio.emit('thread_status_changed')

    def resume_thread(self, name):
        if name in self.pause_events:
            self.pause_events[name].clear()
            socketio.emit('thread_status_changed')

    def get_active_threads(self):
        return {
            name: {
                'is_alive': thread.is_alive(),
                'status': 'paused' if self.pause_events.get(name, Event()).is_set() else 'running'
            }
            for name, thread in self.threads.items()
            if thread.is_alive()
        } 

thread_manager = ThreadManager()
