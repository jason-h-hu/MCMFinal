import bs4 
import os
import sys
import re
import dateutil.parser

def tokenize(rawString):
	words = re.split("\s+", rawString)
	words = [word for word in words if len(word) > 0]
	words = ["@START"] + words + ["@END"]
	return words

def sentiment(tokenizedString):
	return 0

def formatDate(dateString):
	currentDate = dateString
	currentDate = currentDate.split(" ")
	currentDate = currentDate[0]
	currentDate = currentDate.split("-")
	currentDate = "-".join(currentDate[:2])
	return currentDate

def parseMessage(message):
	username = message.find_all(class_="user")[0].string
	date = message.find_all(class_="meta")[0].string
	text = message.next_sibling.string
	text = "" if text == None else text
	text = text.encode('utf-8')
				
	return username, date, text

def jaccard(set1, set2):
	return float(len(set1.intersection(set2))) / len(set1.union(set2))

def representation(set1, set2):
	return float(len(set1.intersection(set2))) / len(set1)

def ngram(words, n):
	ngram = words[:-n]
	for i in range(1, n):
		ngram = zip(ngram, words[i:])
	return ngram

class Stemmer(object):
	"""docstring for Stemmer"""
	def __init__(self):
		super(Stemmer, self).__init__()
		self.stop = []
		try:
			with open("stopwords.txt") as stopFile:
				for word in stopFile.readlines():
					self.stop.append(word.strip())
		except Exception, e:
			self.stop = ["the", "this", "that", "a", "an"]
		
	def cleanAndStem(self, tokens):

		tokens = [token if token not in ["@START", "@END", "@NEWLINE"] else "" for token in tokens]
		words = [token.strip().lower() for token in tokens]

		# Strip punctuations
		words = [re.sub("^[\W_]+", "", word) for word in words]
		words = [re.sub("[\W_]+$", "", word) for word in words]

		# Replace a word contains www. or http(s):// with URL so that we can treat all the urls the same
		words = [re.sub('www\..*', "@URL", word) for word in words]
		words = [re.sub('https?:*', "@URL", word) for word in words]
		words = [re.sub('.*\.com', "@URL", word) for word in words]
		words = [re.sub('.*\.edu', "@URL", word) for word in words]
		words = [re.sub('.*\.gov', "@URL", word) for word in words]
		words = [re.sub('.*\.org', "@URL", word) for word in words]

		# Replace two or more occurrences of the same character with two occurrences. i.e. 'exciteddddd' to 'excitedd'
		words = [re.sub(r'([a-z])\1+', r'\1\1', word) for word in words]

		# Use the stop words list to filter out low value words such as 
		# 'the', 'is' and 'on'.
		# words = [word if word not in self.stop else "" for word in words]
		words = self.removeStopwords(words)
		# Apply stemming using Porter Stemmer. Please refer to the python 
		# implementation (porter_stemmer.py) as well as the example usage 
		# file (porter_stemmer_example.py).
		return words

	def removeStopwords(self, tokens):
		words = [word if word not in self.stop else "" for word in tokens]
		for word in words:
			if len(word) > 0:
				return words
		return tokens

