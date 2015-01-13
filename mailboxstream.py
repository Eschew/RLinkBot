#mailboxstream.py is part of the RedditLinkParseBot project
#Runs simultaneously with the program. This thread checks 
#the mailbox to determine if there are any messages that 
#need to be respond to.
#Runs by multithreading in the original python project. 
#The general nature of this script means that it isn't
#solely designated for the RedditLinkParseBot
#This project requires on the log_writer module

#Multithread class is not infinite, the main thread must
#the mailboxstream thread


#Andrew Liu

import praw, time, re, string, threading, time, sys
from log_mod import log_writer

#credential_location is the location of the username password in a txt file
#log_location is the location where the log_writer is writing logs too
class mailbox_operation(threading.Thread):
	def __init__(self, cred_info, log_location, id_name = "Mailbox"):
		try:
			threading.Thread.__init__(self)
			self.log = log_writer(log_location, id_name)
			self.log.append("Mailboxscript start")
			self.__log_in(cred_info)
			self.can_run = True
			self.perm_end = False
		except Exception as e:
			self.log.crash_handling("Unsucessful startup: "+str(e))
			exit()

		self.start()

	def __log_in(self, cred_info):
		try:
			openFile = open(cred_info, "r")
			self.__r = praw.Reddit("Mailbox search script")
			self.bot_username = openFile.readline().strip()
			self.__r.login(self.bot_username, openFile.readline().strip())
			self.log.append("Successful login")
			self.ready = True
			openFile.close()
		except Exception as e:
			self.log.crash_handling("Unsucessful login: "+str(e))
			self.ready = False
			openFile.close()
			exit()
		self.log.append("Ready to run thread")

	def toggle_pause(self):
		if (self.can_run):
			self.log.append("Paused mailbox thread")
		else:
			self.log.append("Resumed mailbox thread")
		self.can_run = not self.can_run

	def turn_off(self):
		self.log.append("Permanently ended thread")
		self.perm_end = True
		self.log.close()

	def run(self):
		while(True):
			if(self.perm_end):
				break;
			else:
				if(self.can_run):
					self.process()
			time.sleep(10)

	def emergency_exit(self, error):

		self.log.append("Emergency exit: "+str(error)+" Line: "+str(sys.exc_info()[-1].tb_lineno))
		self.turn_off()

	def process(self):
		self.log.append("Starting mailbox loop")
		try:	
			mb = self.__r.get_unread(limit=None)
			for message in mb:
				if re.search("^delete", message.body.lower()):
					replied_comment = self.__r.get_info(thing_id = "t1_"+message.id)
					self.log.append("Message found")
					if(not replied_comment.is_root):
						parent_of_replied = self.__r.get_info(thing_id = replied_comment.parent_id)
					else:
						self.log.append("Message skipped due to having no parent comment: t1_"+message.id)
						message.mark_as_read()
						continue

					if(not parent_of_replied.is_root):
						grandparent_of_replied = self.__r.get_info(thing_id = parent_of_replied.parent_id)
					else:
						self.log.append("Messages skipped: Grandparent does not exist: t1_"+message.id)
						message.mark_as_read()
						continue
					try:
						print(parent_of_replied.author.name.lower() == self.bot_username.lower() and grandparent_of_replied.author.name.lower() == message.author.name.lower())
						if(parent_of_replied.author.name.lower() == self.bot_username.lower() and grandparent_of_replied.author.name.lower() == message.author.name.lower()):
							parent_of_replied.delete()
							self.log.append("Sucessfully delete comment: t1_"+message.id)
							message.mark_as_read()
						else:
							self.log.append("Unsuccessfully deleted comment: original user did not call for delete: t1_"+message.id)
							message.mark_as_read()
					except AttributeError as e:
						if(str(e) == "'NoneType' object has no attribute 'name'"):
							parent_of_replied.delete()
							self.log.append("Successfully deleted orphan comment: t1_"+message.id)
							message.mark_as_read()		

		except Exception as e:
			self.log.crash_handling("Fatal error in runtime thread: "+str(e))

		self.log.append("End mailbox loop")






