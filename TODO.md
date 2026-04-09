1. Add client receipt generation to PDF
    upon payment for job, there should be two buttons
     - Button 1 - download receipt (which will have client name, job details, amount paid, date and time)
     - Button 2 - send sms (which will send an sms to the client's phone number - sms comtent will be a link to view the online receipt without logging in - should have a UUID for receipts)




2. Client Database
    - When creating a job, entering the client name should check db for matching clients and selected one should populate form
    - Create new client if does not exist
    - PK for client should be phone number
    - Clients without phone numbers should be put under one group