Need to confirm booking before the agent books an email

Approach selected:
agent uses booking tool, but inserts as pending, and an email is sent for confirmation. When user clicks to confirm, it lands on a webhook with a verification id. 

A Rejected decision: langgraph interrupt, which pauses the checkpoint or something similar. Not good if multiple users are using the tool at the same time to book, because one business has only one thread id. This thread id checkpoint/memory will reset after a period of time as checkpoint memory for long periods is not the point.


