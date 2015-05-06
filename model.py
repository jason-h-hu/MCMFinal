from collections import defaultdict
import bs4 
import os
import sys
import random
from chatbot import generateMonths
from textParse import *
import json
import datetime

def findProfileFile(profileFile):
	# print "remember! I'm testing!"
	# return "test.htm"

	if not os.path.exists(profileFile):
		print "Cannot find", profileFile
		return

	pathToChats = profileFile + "/html/messages.htm"

	if not os.path.exists(pathToChats):
		print "Cannot find the messages.html in", pathToChats
		return

	return pathToChats

def buildConversation(messages, name):
	conversation = []
	currentSpeaker = name
	currentText = ""
	currentDate = None
	for message in messages:
		username, date, text = parseMessage(message)
		tempDate = dateutil.parser.parse(date)
		if currentDate != None:
			if abs(tempDate - currentDate) > datetime.timedelta(0, 60*60*4):
				returnConversation = conversation[:]
				returnConversation.reverse()
				returnDate = formatDate(str(currentDate))
				yield returnConversation, formatDate(str(currentDate))
				conversation = []
				currentSpeaker = name
				currentText = ""
		currentDate = tempDate
		if username == currentSpeaker:
			currentText = text + " @NEWLINE " +  currentText
		else:
			conversation.append((currentSpeaker, currentText))
			currentSpeaker = username
			currentText = text
	conversation.append((currentSpeaker, currentText))
	conversation.reverse()
	yield conversation, formatDate(str(currentDate))


def buildModel(profileFile):

	pathToChats = findProfileFile(profileFile)
	stemmer = Stemmer()

	# maps from date -> w1 -> w2 -> count for P(w2|w1)
	# markovModel = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
	# responseModel = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
	# frequency = defaultdict(lambda:defaultdict(float))
	# wordCount = defaultdict(int)

	# maps from date -> list of repsonses
	prompts = defaultdict(list)

	# maps from date -> w -> list of indices
	reverseIndex = defaultdict(lambda:defaultdict(list))

	with open(pathToChats) as chatFile:
		print "Loading into soup ..."
		soup = bs4.BeautifulSoup(chatFile)
		print "Loaded into soup."

		# name = "Jason Hu"
		name = soup.title.string.split(" - ")
		name = name[0]
		print "Is your name", name, "?"

		print "Looking through soup ..."
		for thread in soup.find_all("div", class_="thread"):

			for conversation, currentDate in buildConversation(thread.find_all(class_="message"), name):
				prevBagOfWords = set()
				prevSpeaker = ""
				prevPrompt = ""
				for username, text in conversation:
					tokenizedText = tokenize(text)
					if len(tokenizedText) > 2:
						if username == name:

							# # BUILD RESPONSE
							# for word in tokenizedText:
							# 	for prevWord in prevBagOfWords:
							# 		responseModel[currentDate][prevWord][word] += 1

							# # BUILD FREQUENCY
							# cleanedText = stemmer.cleanAndStem(tokenizedText)
							# cleanedText = [word for word in cleanedText if len(word) > 0]
							# for word in cleanedText:
							# 	frequency[currentDate][word] += 1
							# wordCount[currentDate] += len(cleanedText)

							# BUILD INVERTED INDEX
							# if currentDate not in prompts:
							# 	print "now seen", currentDate
							prompts[currentDate].append({ 
								"time": currentDate, 
								"prompt": {
									"speaker": prevSpeaker,
									"tokens": list(prevBagOfWords),
									"text": prevPrompt
								}, 
								"response": {
									"speaker": username,
									"text": text 
								}
							})
							index = len(prompts[currentDate]) - 1
							for word in prevBagOfWords:
								reverseIndex[currentDate][word].append(index)

							# # BUILD BIGRAM
							# bigram = zip(tokenizedText[:-1], tokenizedText[1:])
							# for a, b in bigram:
							# 	markovModel[currentDate][a][b] += 1

						else:
							prevSpeaker = username
							prevPrompt = text
							prevBagOfWords = set([word for word in stemmer.cleanAndStem(tokenize(prevPrompt)) if len(word) > 0])

	return {
				# "markov": markovModel, 
				# "response": responseModel,
				# "frequency": frequency,
				# "count": wordCount,
				"prompts": prompts,
				"reverseIndex": reverseIndex
			}

def transferToDefaultDict(defdict, regdict):
	for key, value in regdict.iteritems():
		if isinstance(value, dict):
			defdict[key] = transferToDefaultDict(defdict[key], value)
		else:
			defdict[key] = value
	return defdict

def loadModel(modelFile):
	print "loading model ..."
	with open(modelFile) as model:
		rawModel = json.load(model)
		defdicts = {	
						# "markov": defaultdict(lambda:defaultdict(lambda:defaultdict(int))), 
						# "response": defaultdict(lambda:defaultdict(lambda:defaultdict(int))),
						# "frequency": defaultdict(lambda:defaultdict(float)),
						# "count": defaultdict(int),
						"prompts": defaultdict(list),
						"reverseIndex": defaultdict(lambda:defaultdict(list))
					}
		return {key: transferToDefaultDict(value, rawModel[key]) for key, value in defdicts.iteritems()}
		# for key, value in transferedDicts["prompts"].iteritems():
		# 	for convo in value:
		# 		print convo["response"]["text"]

	print "ERROR! I don't think that's a model"
	return {}

def saveModel(languageModel, modelFile):
	print "saving model ..."
	with open(modelFile, 'w') as model:
		json.dump(languageModel, model)
		return
	print "ERROR! I don't think that's a model"
