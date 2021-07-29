# forum-parser
Hackers forum parser

We collect data about cybercriminals' activity from a group of underground hacking forums, which helps us later to identify and gather evidence about them. We do this by parsing the contents of these forums using Python scripts and the magical power of Regular Expressions.
We start by parsing information about the activity on the forum, by visiting the “feed” page, where we can see the new messages in threads (Topics) and when they were posted. Next step is to go to each of these topics and parse all the messages inside it. The result of this task is 3 lists of dictionaries: one for all the topics we parsed from the feed page, one for all the messages we parse from each of the topics we parsed in the feed page, and one for all the forum members who posted messages in the pages we parsed.
The script should be written so it checks for new messages in the feed page, and it parses all the new topics and the messages in them that are new.

Practical example:

1. Go to the page using python with Tor and get the source code of the page.
2. Write regular expressions to catch the:
   * Topic names which have new messages
   *	URLs to these topics
   *	Datetime of the last message
   *	Number of replies to the topic
3. Use these regexes to catch and store a list of dictionaries for the previous information.
4. For each topic in the list, you need to generate a special hash build from:
   *	The topic name
   * The number of replies to the topic
   *	The datetime of the last message
5. For each of the URLs for topics you collected in the previous step, you need to get this page and parse the following data, like we did with the feed page (using regular expressions):
   * The message text
   * The message datetime
   *	The message author name
   *	The message URL
6. For each message, you have to generate special hash built from the following fields:
   *	The message text
   *	The message datetime
   *	The message author name
   *	The message URL
7. We also need to create a dictionary list of members who wrote the messages, and it will contain:
   *	The member’s name
   *	The member’s reputation
   *	The member’s number of messages 
   *	Save the author’s profile picture in Base64 Format
8. Like with the rest, a special hash for each member must be calculated using:
   *	The member’s name
   *	The member’s number of messages
