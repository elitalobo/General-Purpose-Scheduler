import heapq
import sys
#import queue
import time
from collections import namedtuple
import time
import threading
import dummy_threading
import smtplib

num_workers = 10
class Empty(Exception):

    "Exception raised by PriorityQueue.get(block=0)/get_nowait()."

    pass


class Full(Exception):

    "Exception raised by PriorityQueue.put(block=0)/put_nowait()."

    pass

__all__ = ['event_scheduler']

Event = namedtuple('Event', 'time,priority,action,params')

class PriorityQueue:
	""" Priority Queue maintains task in the order in which it is supposed to be executed"""
	def __init__(self, maxsize=0):
		self.maxsize = maxsize
		self._init(maxsize)
		self.mutex = threading.Lock()
		self.not_empty = threading.Condition(self.mutex)
		self.not_full = threading.Condition(self.mutex)
		self.all_tasks_completed = threading.Condition(self.mutex)
		self.unfinished_tasks = 0
	
	def task_completed(self):
		""" When a task is completed, it decreases the unfinished_task count"""
		self.all_tasks_completed.acquire()
		try: 
			unfinished = self.unfinished_tasks-1
			if unfinished <=0:
				if unfinished < 0:
					raise ValueError('tasks completed! this module is called too many times!')
				self.all_tasks_completed.notify_all()
			self.unfinished_tasks = unfinished
		finally:
			self.all_tasks_completed.release()
	
	def join(self):
		""" When all the workers finish their task, they will be reassingned remaining tasks """
		self.all_tasks_completed.acquire()
		try:
			while self.unfinished_tasks:
				self.all_tasks_completed.wait()
		finally:
			self.all_tasks_completed.release()

	def size(self):
		""" Returns size of queue """
		self.mutex.acquire()
		n = self.pqsize()
		self.mutex.release()
		return n

	def full(self):
		""" Checks if queue is full """
		self.mutex.acquire()
		n = 0 < self.maxsize == self.pqsize()
		self.mutex.release()
		return n
		
	def put(self, item, block=True, timeout=None):
		""" Adds event into the queue"""
		self.not_full.acquire()
		try:
			if self.maxsize > 0:
				if not block:
					if self.pqsize() == self.maxsize:
						raise Full
			elif timeout is None:
				while self.pqsize() == self.maxsize:
					self.not_full.wait()
			elif timeout < 0:
				raise ValueError("Timeout should be non negative no")
			else:
				end = time.time() + timeout
				while self.pqsize() == self.maxsize:
					remaining = end - time()
					if remaining <= 0.0:
						raise Full
					self.not_full.wait(remaining)
			self._put(item)
			self.unfinished_tasks +=1
			self.not_empty.notify()
		finally:
			self.not_full.release()

	def put_without_wait(self, item):
		""" Adds task to the queue without blocking it for sometime """
		return self.put(item, False)

	def get(self, block=True, timeout=None):
		""" Removes task from queue if any and returns it for execution """
		self.not_empty.acquire()
		try:
			if not block:
				if not self.pqsize():
					raise Empty
			elif timeout is None:
				while not self.pqsize():
					self.not_empty.wait()
			elif timeout < 0:
				raise ValueError("Timeout should be non-negative")
			else:
				end = time.time() + timeout
				while not self.pqsize():
					remaining = end - time.time()
					if remaining < 0.0:
						raise Empty
					self.not_empty.wait(remaining)
			item = self._get()
			self.not_full.notify()
			return item
		finally:
			self.not_empty.release()
	
	def get_without_wait(self):
		""" Get task from queue without  getting blocked for sometime """
		return self.get(False)

	def _init(self, maxsize):
		""" Creates a new queue """
        	self.queue = []


   	def pqsize(self, len=len):
		""" Returns no of elements in the queue """
        	return len(self.queue)


    	def _put(self, item, heappush=heapq.heappush):
		""" Adds task to the queue. Heapq is used to maintain the tasks in the order of execution"""
        	heapq.heappush(self.queue, item)


    	def _get(self, heappop=heapq.heappop):
		""" Gets highest priority task from queue """
        	return heappop(self.queue)

	
    	def remove(self, event, block=None):
		""" Removes task from queue if it hasn't been executed """
	 	self.not_empty.acquire()
                try:
                	if not self.pqsize():
                        	raise Empty
			else:
				try:
					self.queue.remove(event)
        				heapq.heapify(self.queue)
				except:
					raise ValueError("Event not present in queue!")
				self.not_full.notify()
				self.unfinished_tasks -= 1
		finally:
			self.not_empty.release()

	def execute(self,item):
		"""Calls teh function associated with the task"""
		print "Doing task " + str(item.action)
		item.action(*(item.params))
		print "done"

        def work(self):
		""" Work is assigned to a worker """
                while True: 
                        item = self.get()
			while (time.time() < item.time):
				time.sleep(1)	
                        self.execute(item)
                        time.sleep(1)
                        self.task_completed()

class event_scheduler:
	""" Allows user to add events, remove events,run scheduler and view time expired at any point of time """
	def __init__(self,delay=0):
		""" Creates a new priority queue of max size 1000"""
		self._queue = PriorityQueue(maxsize=1000)
		self.cur_time = time.time()
		self.delay_time = delay #if delay is required to compensate for time lost while adding tasks
	
	def add_event(self, time, priority, action, params):
		""" Adds event to queue. Takes the time of execution, priority, action and parameters required to perform the action as arguments"""
		time = self.cur_time + time
		event = Event(time,priority,action,params)
		self._queue.put(event)
		return event

	def cancel_event(self, event):
		""" Allows user to remove invalid events from the queue using the event id returned at the time of adding event to the queue"""
		self._queue.remove(event)
		
	def empty(self):
		""" checks if queue is empty """
		return not self._queue

	def run(self):
		""" Creates workers to execute events from the queue """
		for i in range(num_workers):
     			worker = threading.Thread(target=self._queue.work)
     			worker.setDaemon(True)
     			worker.start()
		self._queue.join()      

	def print_time(self):
		""" Prints time (in seconds) expired """
               	time_in_secs = time.time() - self.cur_time
	       	return "Timer: " + str(time_in_secs)
		
		
def test_task1(*args):
	print "Executing Task 1"

def test_task2(*args):
	print "Executing Task 2"

def test_task3(*args):
	print "Executing Task 3"			

def test_send_birthday_email(*args):
	if(len(args)<4):
		print "Unsuccessful. Missing parameters!"
		return
	sender = args[0]
	receivers = [args[1]]
	message = "Subject:" + args[2] + "\n" + args[3]


	try:
   		smtpObj = smtplib.SMTP('localhost')
  		smtpObj.sendmail(sender, receivers, message)         
   		print "Successfully sent email"
	except:
   		print "Error: unable to send email"
