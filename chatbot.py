import sys
import random
import math
from textParse import *
from collections import defaultdict
import time

def startChatbot(languageModel):
	print "HELLO! Welcome to the Android Memories."
	print "Hit CTRL + D to quit"

	print ""
	print "Which younger self would you like to speak with? Please provide a date as a year and month. e.g. 2011-10"
	sys.stdout.write("> ")
	date = sys.stdin.readline().strip()

	chatBot = Chatbot(languageModel, date)
	while True:
		sys.stdout.write("> ")
		line = sys.stdin.readline()
		if len(line) == 0:
			break
		print chatBot.generateResponse(line)

# TAKES  IN A WORD -> COUNT DICT
# RETURNS THE LOG PROBABILITY OF ALL THE WORDS, AS A DICT
# WORD -> LOG PROB
def calculateLogProb(dictionary, smooting=True):
	items = [(word, count) for word, count in dictionary.iteritems()]
	total = sum([count for word, count in items])
	if total == 0:
		return defaultdict(float)
	logProbDict = defaultdict(lambda : math.log(1.0/total)) if smooting else defaultdict(float)

	for word, count in items:
		logProbDict[word] = math.log(float(count)/float(total)) 
	return logProbDict

# COMBINES TWO DEFAULTDICTS INTO ONE. 
def mergeDicts(dict1, dict2):
	for key, value in dict2.iteritems():
		dict1[key] += value
	return dict1

# Takes in a {key: val ...} and picks a key at random, weighted by val
# Returns a key
def weightedChoice(candidates):

	elements = [(score, word) for word, score in candidates.iteritems()]
	return weightedChoice2(elements)[1]

# Takes in a list of tuples (val, field1, field2 ...) and
# picks and returns a random tuple, weighted by val
def weightedChoice2(candidates):

	elements = candidates
	elements.sort()
	elements.reverse()

	total = sum(map(lambda x:x[0], elements))
	pivot = random.random()*total
	counter = 0

	for i in range(len(elements)):
		score = elements[i][0]
		counter += score
		if counter <= pivot:
			return elements[i]

	print "error with selecting markov choice <------"
	return elements[0]

# Generator for a string of the form "year-month"
def generateMonths(date, numMonths=24):
	yield date
	date = date.split("-")
	year = int(date[0])
	month = int(date[1])
	for i in range(numMonths):
		if month == 1:
			month = 12
			year -= 1
		else:
			month -= 1
		yield str(year) + "-" + str(month).zfill(2)

# Dictionary is a mapping of
# date -> w1 -> w2 -> count
# This should return a dictionary that is a mapping
# of w1 -> w2 -> count
# That is representative of the idiolect at that date
def assembleCountByDate(dictionary, date, d=0.9):
	counts = defaultdict(lambda: defaultdict(float))
	counter = 1.0
	for date in generateMonths(date):
		curCount = dictionary[date]
		for w1, value in curCount.iteritems():
			for w2, count in value.iteritems():
				counts[w1][w2] += count*counter
		counter *= d
	return counts

# Dictionary is a mapping of
# date -> word -> count
# This should return a dictionary that is a mapping
# of word -> count
# That is representative of the idiolect at that date
def assembleCountByDate2(dictionary, date, d=0.9):
	counts = defaultdict(float)
	counter = 1.0
	for date in generateMonths(date):
		curCount = dictionary[date]
		for word, count in curCount.iteritems():
			counts[word] += counter * count
		counter *= d
	return counts	

# Dictionary is a mapping of
# date -> count
# This should return a count
# That is representative of 
# the size of the idiolect
def assembleCountByDate3(dictionary, date, d=0.9):
	counts = 0
	counter = 1.0
	for date in generateMonths(date):
		counts += dictionary[date]*counter
		counter *= d
	return counts	

def printDict(dictionary, n=10):
	printout = [(key, value) for key, value in dictionary.iteritems()]
	printout.sort(key=lambda x: x[1])
	for key, value in printout[-n/2:]:
		print key, "\t->\t", value
	print "..."
	for key, value in printout[:n/2]:
		print key, "\t->\t", value
	print ""


class Chatbot(object):
	"""docstring for Chatbot"""
	def __init__(self, languageModel, date):
		super(Chatbot, self).__init__()
		print "Making chatbot ..."
		self.stemmer = Stemmer()
		self.languageModel = languageModel
		# self.updateDate(date)
		print "finsihed making chatbot"

	def updateDate(self, date):
		self.date = date

		# self.responseModel = self.assembleDateAndGetLogProb(self.languageModel["response"])
		# self.markovModel = self.assembleDateAndGetLogProb(self.languageModel["markov"])
		# self.frequency = assembleCountByDate2(self.languageModel["frequency"], date, 1.0)
		# self.count = assembleCountByDate3(self.languageModel["count"], date, 1.0)

		self.reverseIndex = self.languageModel["reverseIndex"]
		self.prompts = self.languageModel["prompts"]

		for date, value in self.reverseIndex.iteritems():
			print date, [word for word, v in value.iteritems()][:10]

		# for date, prompt in self.prompts.iteritems():
		# 	print date, map(lambda x: x["response"]["text"], prompt)


	# Takes in a single string, as a prompt
	# Returns a string, as a response. Either through
	# a reverse index lookup or a markov chain
	def generateResponse(self, message):
		candidates = self.invertedIndexResponses(message)
		if len(candidates) == 0:
			return ""
			# print "PROBABILISTICS"
			# return self.generateProbabilisticResponse(message)
		candidates = [(score, candidate["response"]["text"]) for score, candidate, word in candidates]
		response = weightedChoice2(candidates)
		response = response[1].split(" ")
		response = self.formatResponse(response)
		return response

	# Takes in a single string as a prompt
	# Returns a list of possible responses. 
	# The list is stored as a tuple of their
	# (jaccard similarity, the conversation, word from test prompt)
	# Conversations are formatted as 
	# { 
	# 	"time": currentDate, 
	# 	"prompt": {
	# 		"speaker": prevSpeaker,
	# 		"text": prevPrompt
	# 	}, 
	# 	"response": {
	# 		"speaker": username,
	# 		"text": text 
	# 	}
	# }
	def generateResponses(self, message):
		return self.invertedIndexResponses(message)

	# Takes in a string. Returns a string. 
	def generateProbabilisticResponse(self, message):
		response = self.probabilisticResponse(message)
		return self.formatResponse(response)


	# Given a prompt, it does a reverse-index lookup
	# and returns a list of candidate conversations
	# as (score, conversation, word from prompt)
	# Conversations are formatted as
	# { 
	# 	"time": currentDate, 
	# 	"prompt": {
	# 		"speaker": prevSpeaker,
	# 		"token": []
	# 		"text": prevPrompt
	# 	}, 
	# 	"response": {
	# 		"speaker": username,
	# 		"text": text 
	# 	}
	# }
	def invertedIndexResponses(self, message):
		message = tokenize(message)
		tokenMessage = self.stemmer.cleanAndStem(message)
		tokenMessageSet = set(tokenMessage)
		candidates = []
		counter = 1.0

		numConversations = 100
		numConvoPerWord = int(math.ceil(numConversations/len(tokenMessageSet)))

		for i in range(len(tokenMessage)):
		
			if message[i] in ["@START", "@END"]:
				continue
			token = tokenMessage[i]
			if len(token) == 0:
				continue


			tempCandidates = []
			for month in generateMonths(self.date):
				candidateIndices = self.reverseIndex[month][token]
				if len(candidateIndices) == 0:
					continue
				candidateResponses = [self.prompts[month][index] for index in candidateIndices]
				for response in candidateResponses:
					prompt = set(response["prompt"]["tokens"])
					score = -jaccard(tokenMessageSet, prompt)*counter
					response["response"]["text"] = self.formatResponse(response["response"]["text"] .split(" "))
					response["prompt"]["text"] = self.formatResponse(response["prompt"]["text"] .split(" "))
					tempCandidates.append((score, response, message[i]))
			candidates += tempCandidates[:numConvoPerWord]
			counter *= 0.9
		return candidates


	def probabilisticResponse(self, message):
		mostSalientWord = self.getMostSalientWord(tokenize(message))
		responseDict = self.responseModel[mostSalientWord]

		response = ["@START"]
		prevWord = response[-1]
		while prevWord != "@END":

			candidates = defaultdict(lambda:math.log(1.0/self.count))
			candidates = mergeDicts(candidates, self.markovModel[prevWord])

			currentResponse = {key: responseDict[key]*2 for key, _ in candidates.iteritems()}

			candidates = mergeDicts(candidates, currentResponse)
			response.append(weightedChoice(candidates))
			prevWord = response[-1]
		return response[1:-1]

	# takes in a date -> w1 -> w2 -> count dictionary
	# returns a w1 -> w2 -> log prob dictionary
	def assembleDateAndGetLogProb(self, dictionary):
		scaledResponse = assembleCountByDate(dictionary, self.date)
		assembledDict = defaultdict(lambda:defaultdict(float))
		for w1, countDict in scaledResponse.iteritems():
			assembledDict[w1] = calculateLogProb(countDict)
		return assembledDict

	def formatResponse(self, response):
		response = [r if r != "@NEWLINE" else "\n" for r in response]
		return " ".join(response)

	def getMostSalientWord(self, tokenMessage):
		mostSalientWord = ""
		mostSalientWordScore = float('inf')
		for token in self.stemmer.cleanAndStem(tokenMessage):
			if len(token) > 0 and token in self.frequency:
				score = math.log(self.frequency[token]/self.count)
				if score < mostSalientWordScore:
					mostSalientWord = token
					mostSalientWordScore = score
		return mostSalientWord