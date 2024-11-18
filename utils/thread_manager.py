from threading import Thread, Event
from queue import Queue
import logging
from utils.socket_manager import socketio
import time
import ctypes


class StoppableThread(Thread):
    def __init__(self, target, args, **kwargs):
        # Extract or create control events
        self._stop_flag = args[-3]  # stop_event
        self._pause_flag = args[-1]  # pause_event
        self._state = "running"

        # Call parent constructor with modified target
        super().__init__(target=self._wrapped_target, args=(target, args), **kwargs)

    def _wrapped_target(self, original_target, args):
        try:
            while not self._stop_flag.is_set():
                if self._pause_flag.is_set():
                    time.sleep(0.1)
                    continue
                original_target(*args)
                break
        except Exception as e:
            logging.error(f"Thread error: {e}")
        finally:
            self._state = "stopped"

    def stop(self):
        self._stop_flag.set()
        self._state = "stopped"

    def pause(self):
        self._pause_flag.set()
        self._state = "paused"

    def resume(self):
        self._pause_flag.clear()
        self._state = "running"

    def get_state(self):
        return self._state


class ThreadManager:
    def __init__(self):
        self.threads = {}
        self.log_queue = Queue()

    def start_thread(self, name, target, args=()):
        if name in self.threads and self.threads[name].is_alive():
            return False

        # Create default events for thread control
        stop_event = Event()
        pause_event = Event()

        # Combine the provided args with our control events and log queue
        thread_args = (*args, stop_event, self.log_queue, pause_event)

        thread = StoppableThread(
            target=target,
            args=thread_args,
            name=name,
            daemon=True
        )

        self.threads[name] = thread
        thread.start()
        socketio.emit('thread_started')
        return True

    def stop_thread(self, name):
        if name in self.threads:
            thread = self.threads[name]
            thread.stop()
            if name in self.threads:
                del self.threads[name]
            socketio.emit('thread_stopped', {'name': name})

    def pause_thread(self, name):
        if name in self.threads:
            thread = self.threads[name]
            thread.pause()
            socketio.emit('thread_status_changed')

    def resume_thread(self, name):
        if name in self.threads:
            thread = self.threads[name]
            thread.resume()
            socketio.emit('thread_status_changed')

    def get_active_threads(self):
        return {
            name: {
                'is_alive': thread.is_alive(),
                'status': thread.get_state()
            }
            for name, thread in self.threads.items()
            if thread.is_alive()
        }


thread_manager = ThreadManager()
