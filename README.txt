To test the functions of the library, run the following commands:

>> import birthday_scheduler as bs
>> import time
>> test1 = bs.test_task1
>> test2 = bs.test_task2
>> test3 = bs.test_send_birthday_email
>> e = bs.event_scheduler()
>> e.print_time
>> e.add_event(100,1,test1,())
>> e.add_event(101,2,test2,())
>> e.add_event(104,3,test3,("xyz.gmail.com","xyz.gmail.com","HP","HP",))
>> e.cancel_event(event_id)
# In the above command -> add the event_id of any of the events added to the queue (It should be of the form -> bs.Event(...))
>>e.run()

