# A python class for easy writing to files in the same location as the
# original python program
#

# Andrew Liu

import datetime


class log_writer:
	'''
	Wrapper class for writing to a single log as a txt file
	__log_name: File destination where logs are being stored
	__module_name: Name of the log_writer to distinguish multithreading

	'''

	def __init__(self, file_address, module=None):
		'''
		file_address - The file dir where logs are being stored
		module - If multiple threads are writing to a single file, 
			module name distinguishes between different threads.
			This variable is assigned upon initiation
		'''
		self.__log_name = file_address
		self.__module_name = module
		try:
			self.__file = open(file_address, "r")
			print("Open file at "+file_address)
			self.__file = open(file_address, "a")
			self.append("\n_____________________________\nOpen Log Operation")
		except(FileNotFoundError):
			try:
				self.__file = open(file_address, "a")
				print("New File at "+file_address)
				self.append("Log created")

			except Exception as e:
				self.file_address = None
				print(e)

	def module_name(self):
		return self.__module_name

	def file_name(self):
		return self.__log_name

	def append(self, string):
		'''
		string - The log message being stored
		module - If multiple logs writing to 
		'''
		if(self.__file.closed):
			print("already closed")
		else:
			self.__file = open(self.__log_name, "a")

			current_time = datetime.datetime.now();
			current_year = str(current_time.year);
			current_month = str(current_time.month);
			current_day = str(current_time.day);
			current_hour = str(current_time.hour);
			current_minute = str(current_time.minute);
			current_second = str(current_time.second);
			AM_PM = "AM"

			if(int(current_hour)>12):
				current_hour = str(int(current_hour)-12)
				AM_PM = "PM"

			if(len(current_month)<2):
				current_month = "0"+current_month

			if(len(current_day)<2):
				current_day = "0"+current_day

			if(len(current_hour)<2):
				current_hour = "0"+current_hour

			if(len(current_minute)<2):
				current_minute = "0"+current_minute

			if(len(current_second)<2):
				current_second = "0"+current_second

			time_stamp = "["+current_year+"-"+current_month+"-"+current_day+" "+current_hour+":"+current_minute+":"+current_second+" "+AM_PM+"]"

			if(self.__module_name is None):
				time_stamp = time_stamp+" ~ "+string
			else:
				time_stamp = time_stamp+" ~ "+self.__module_name+": "+string
			self.__file.write(time_stamp+"\n")

	def read_log(self):
		'''
		Reads the entire log so far
		'''
		if(self.__file.closed):
			print("already closed")
		else:
			self.__file.close()
			self.__file = open(self.__log_name, "r")
			print(self.__file.read())

	def crash_handling(self, string):
		'''
		Use this to record errors/crashes in the main program
		Use in just the final try/except clause to catch any unhandled
		error/exception
		'''
		if(self.__file.closed):
			print("already closed")
		else:
			self.append("**CRASH** "+string)
			self.close()


	def close(self):
		'''
		Records when the log was closed and closes the file
		'''
		if(self.__file.closed):
			print("already closed")
		else:
			self.append("Close Log Operation\n_____________________________\n")
			self.__file.close()



