import argparse
import datetime
from model import *
from chatbot import *

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired

# parser = argparse.ArgumentParser()
# parser.add_argument('-profile', type=str, help='The directory containing the summary of the Facebook profile')
# parser.add_argument('-model', type=str, help='Load a pre-computed model')
# parser.add_argument('-save', type=str, help='Compute a language model and save to this file')
# args = parser.parse_args()

# startChatbot(model)
model = loadModel("model.json") # buildModel(args.profile) if args.profile != None else loadModel(args.model)
# if args.save != None:
# 	saveModel(model, args.save)
chatBot = Chatbot(model, "2012-05")

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/', methods=["GET", "POST"])
def index():
	if request.method == 'POST':
		print request.form
		date = request.form["year"] + "-" + request.form["month"]
		chatBot.updateDate(date)
		return redirect("/chat")

	return render_template('landing.html')

@app.route('/chat')
def chat():
	return render_template("index.html")

@app.route('/prompt', methods=["GET", "POST"])
def prompt():
	if request.method == 'POST':
		prompt = request.form["prompt"]
		return render_template("message.html", 
			align = "message-right",
			text = prompt,
			timestamp = str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute)
		)# "<p style='text-align:left;'>"+response + "?</p>"
	return ""

@app.route('/response', methods=["GET", "POST"])
def response():
	if request.method == 'POST':
		prompt = request.form["prompt"]
		response = chatBot.generateResponse(prompt)
		return render_template("message.html", 
			align="message-left",
			text=response,
			timestamp=str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute)
		)# "<p style='text-align:left;'>"+response + "?</p>"
	return ""

@app.route('/responseFormat', methods=["GET", "POST"])
def responseFormat():
	if request.method == 'POST':
		response = request.json

		response = response["response"]["text"].split(" ")
		response = chatBot.formatResponse(response)
		returnMessage = render_template("message.html", 
			align="message-left",
			text=response,
			timestamp=str(datetime.datetime.now().hour) + ":" + str(datetime.datetime.now().minute)
		)
		print returnMessage
		return returnMessage
	return ""		

@app.route('/responses', methods=["GET", "POST"])
def responses():

	if request.method == 'POST':
		prompt = request.json
		prompt = prompt["prompt"]
		print "got the prompt"
		responses = chatBot.generateResponses(prompt)
		print "generated responses"
		return json.dumps(responses)
	return ""