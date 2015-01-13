import praw, time, re, string, threading, sys

from mailboxstream import mailbox_operation
from log_mod import log_writer

"""Global Variable """
r = 0 #Variable for the reddit praw wrapper
bot_username = 0 #Bot username

banned_users = [] #List of banned users grabbed from the wikipages
subreddit_ok_list = [] #same
excluded_subs = [] #same

log = log_writer("log.txt", "main_thread") #Log_writer object for recording events
concluding_statement = "\n\n---\n\n*This is a bot! If you summoned this bot by accident, reply with 'delete' to remove it. If you want to stop it from posting on your comments, reply with 'unfollow'. If you would like to continue the bot's comments, reply with 'follow'*"
mailbox = 0 #Future mailthread

def log_in():
	"""
	Creates the reddit praw object and log in the credentials using an external text file

	It is possible for this method to error and enter crash_handling sequence
	"""
	try:
		global r
		global bot_username
		openFile = open('RedditParseBot.txt', 'r')
		r = praw.Reddit("Turns reddit links into texts without opening them /u/iEschew")
		bot_username = openFile.readline().strip()
		r.login(bot_username, openFile.readline().strip())
		log.append('Successfully connected with :'+bot_username)
		openFile.close()
	except Exception as e:
		log.crash_handling('Failed to log into Reddit :'+e)
		openFile.close()
		emergency_exit(e)

def build_mailbox_thread():
	"""
	Creates the mailbox thread to check the inbox for delete, follow, and unfollow

	It is not possible for this error to method generally unless there's a problem with mailboxstream
	"""
	log.append("Attempting to create mailbox thread")
	global mailbox
	mailbox = mailbox_operation("RedditParseBot.txt","log.txt")
	log.append("Successfully made mailbox thread")

def setup_variables():
	"""
	Downloads information from the wiki page

	Generally will not error
	"""
	log.append("Attempt to download user and sub list info")
	global banned_users
	global subreddit_ok_list
	global excluded_subs
	banned_users = r.get_wiki_page('eolabs','bannedusers').content_md.strip().split()
	subreddit_ok_list = r.get_wiki_page('eolabs', 'oksubs').content_md.strip().split()
	excluded_subs = r.get_wiki_page('eolabs', 'excludedsubs').content_md.strip().split()
	log.append("Successfully downloaded user and sub list info")

def is_legal_user(author_name):
	"""
	Determines whether the author_name is in the list of banned_users. The banned_users list
	also includes the bot itself
	"""
	for user in banned_users:
		if user.lower() == author_name.lower():
			return False
	return True	

def convertunix(timestamp):
	"""
	converts timestamp into unix GMT timestampe

	Never fail
	"""
	timestamp = timestamp*1000
	return time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp / 1000.0))


def searchForSubmission(submissionString):
	"""
	Using a submission ID, tries to find the thread
	"""
	if len(submissionString) == 0:
		return None

	try:
		submission = r.get_submission(submission_id = submissionString)
		return submission
	except:
		return None

def main():
	"""
	Using the comment stream to grab a new list of comments. This method
	uses regex to determine whether a link is present in the comment 
	and then isolate the necessary ID's to lockdown the link

	Messiest part of the program
	"""
	for comment in praw.helpers.comment_stream(r, 'lab002', None): #change lab002
		if comment.author is None:
			continue
		elif comment is None:
			continue
		elif is_legal_user(comment.author.name):
			has_link_material = re.findall(r"\/r\/\w*\/comments\/(\w*)\/", comment.body)
			has_permalink_comment = re.findall(r"\/r\/\w*\/comments\/(\w*)\/\w*\/(\w+)",comment.body)
			if(has_link_material is None):
				#There are no link materials in the comment found
				continue
			try:
				#determines whether there are multiple links, multiple links will not trigger
				_ = has_link_material[1]
				continue
			except:
				#There is only one reddit link detected, the following if statements
				#determine if the link is a permalink or submission link
				if has_permalink_comment and has_permalink_comment[0][0] != None:
					#The link leads to a permalink content
					permalink_comment = r.get_info(thing_id="t1_"+has_permalink_comment[0][1]) #permalink content
					submissionThread = searchForSubmission(has_permalink_comment[0][0]) #Submission thread
					if(submissionThread):
						#There exists the submission thread
						string_output = processed_submission(submissionThread, permalink_comment.permalink)
						string_output = add_perma_comment(string_output,permalink_comment)
						log.append("Found permalink for submission_id {0} p_id t1_{1}".format(has_permalink_comment[0][0],has_permalink_comment[0][1]))
						#post_reply(string_output, comment)
					else:
						continue	
				elif has_link_material:
					#for regular link material
					submissionThread = searchForSubmission(has_link_material[0])
					if(submissionThread):
						string_output = processed_submission(submissionThread)
						string_output = processed_norm_comment(string_output, submissionThread)
						if not string_output:
							continue
						log.append("Found submission thread id {0}".format(has_link_material[0]))
						#post_reply(string_output, comment)
					else:
						continue

	log.append("End of main sequence")

def processed_submission(submissionObject, permalink_comment = None):
	"""
	Starts creating the comment body of the response
	"""
	if permalink_comment == None:
		url = submissionObject.permalink
	else:
		url = permalink_comment
	nsfw, upvote, title, self_text, unix_timestamp = submissionObject.over_18, submissionObject.ups, submissionObject.title, submissionObject.selftext, submissionObject.created
	try:
		author = submissionObject.author.name
	except:
		author = "deleted"
	mark_down = "#####&#009;\n\n####&#009;\n\n######&#009;\n"
	return_string = "[**[+"+str(upvote)+"]**"


	if(nsfw):
		return_string = return_string +"**[NSFW]**"

	return_string = return_string+" \""+title+"\" posted by **"+author+"** on "+convertunix(unix_timestamp)+"]("+url+")\n\n"+mark_down
	if(len(self_text) == 0):
		return_string = return_string+"\n\n"
	else:	
		quoteString = re.sub(r"&gt;", ">", self_text)
		quoteString = re.sub(r"&amp;", "&", quoteString)
		quoteString = re.sub(r"\n", "\n>", quoteString)
		return_string = return_string+"\n\n>"+quoteString;

	return return_string;

def processed_norm_comment(return_string, submissionObject):
	"""
	Adds the comment data for the submission thread to the end of the response body
	"""
	return_string = return_string+"\n\nComments:\n\n---\n\n"
	i = 0

	while(i<4):
		try:
			return_string = add_comment_data(return_string, submissionObject._comments[i])
			i = i+1
		except:
			if i == 0:
				return False
			break
		
	return return_string+concluding_statement


def add_perma_comment(return_string, permalink_comment):
	"""
	Instead of processing normal comments and adding 4 comments, this method
	adds the specified permalink
	"""
	return_string = return_string+"  \n\nPermalinked Comment:\n\n---\n\n"

	return_string = add_comment_data(return_string, permalink_comment)
		
	return return_string+concluding_statement

def add_comment_data(return_string, commentObj):
	"""
	Tries to convert the submission's comment into text using regex
	"""
	if commentObj.author is None:
		name = "[deleted]"
	else:
		name = commentObj.author.name
	quoteString = re.sub(r"^", ">", commentObj.body,re.M)
	quoteString = re.sub(r"&gt;", ">", quoteString)
	quoteString = re.sub(r"&amp;", "&", quoteString)
	quoteString = re.sub(r"\n", "\n>>", quoteString)
	quoteString = re.sub(r"&lt;", "<", quoteString)
	return_string = return_string+"\n\n >**[+"+str(commentObj.ups)+"] "+name+"**: \n>"+quoteString+"\n"
	return return_string

def convertunix(timestamp):
	timestamp = timestamp*1000
	return time.strftime("%a %d %b %Y %H:%M:%S GMT", time.gmtime(timestamp / 1000.0))

def check_comment_id(comment):
	"""
	Determines whether the link has already been processed recently
	"""
	for single_comment in comment.replies:
		if single_comment.id in posted_ids:
			return False
	return True

def check_subreddit(comment):
	"""
	Returns whether the subreddit where the comment originates from is a valid sub for use
	"""
	global excluded_subs
	if comment.subreddit.display_name.lower() not in excluded_subs:
		return True
	return False

def post_reply(reply, comment):
	"""
	Void function
	Checks if the reply can be posted and whether if the bot has already responded to reply by recursively calling parent function
	"""
	if check_comment_id(comment) and check_subreddit(comment):
		try:
			if(check_reply_length(reply)):
				a = comment.reply(reply)
				posted_ids.append(comment.id)
				log.append("Reply Posted for "+comment.id)
			else:
				log.append("Comment exceeds maximum length")
		except:
			log.append("Maximum rate limit posted")
	else:
		log.append("bad subs or already posted")

def check_reply_length(reply):
	"""
	Checks if the function is too long
	"""
	if len(reply) > 3000:
		return False
	else:
		return True

def emergency_exit(error):
	"""
	In the event of a catasrophic failure, the program will initiate the emergency_exit which records the log,
	updates the wiki page.
	"""
	log.crash_handling("Emergency exit: "+str(error)+" Line: "+str(sys.exc_info()[2].tb_lineno))
	log.close()
	mailbox.emergency_exit(error)

def save_data():
	b = ""
	for x in banned_users:
		b = b+" "+x

	r.edit_wiki_page("eolabs", "bannedusers", "", b)

	es = ""
	for x in excluded_subs:
		es = es+" "+x

	r.edit_wiki_page("eolabs", "excludedsubs", "", es)

"""Init Sequence"""
try:
	log.append("Starting main sequence")
	log_in()
	build_mailbox_thread()
	setup_variables()
	main()
except KeyboardInterrupt:
	log.append("Keyboard Interrupt end program sequence")
	save_data()


except Exception as e:
	emergency_exit(e)
	exit()


