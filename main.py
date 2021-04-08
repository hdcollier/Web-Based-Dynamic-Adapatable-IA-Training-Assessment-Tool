# This is code is the product of reserach conducted by Henry Collier as a Ph.D. candidate at the University of Colorado Colorado Springs
# This web based code was based on a standalone version of the Dynamic/Adapatable IA assessemnt tool creatd by Henry Collier.
# The web based version of this tool was developed by Henry Collier and Jacob Folsom. 
#The Dynamic/Adaptable IA Training Assessment Tool is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License

from flask import Flask, render_template, request,redirect, url_for, session
import sqlite3 #for db
import re #regix for checking strings for bad chars
import zlib #for hash
import random
import json
import functools
from waitress import serve
app = Flask(__name__, static_folder='static')  
app.secret_key = str(random.randint(1,1000000))
badChars = re.compile('[@_!#$%^&*()<>?/\|}{~:;"\'=\[\]]')

#Register page
@app.route("/", methods=['GET', 'POST'])
def index():
	session.clear()
	#if the user hit submit on index page
	if request.method == "POST":
		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()

		#get data from form on page
		userid = request.form['userID']
		gender = request.form['genderSelect']
		age = request.form['age']
		educationLevel = request.form['educationSelect']
		try:
			if(request.form['unknownKnowBe4Score'] == "on"):
				knownBe4Number = 999.0
		except:
			try:
					knownBe4Number = float(request.form['knownBe4Number'])
			except:
					return render_template('index.html', status="knowBe4NumberNotANumber")
			if knownBe4Number == None:
				return render_template('index.html', status="badknowBe4Number")
		#some checks before passing it to db.
		if len(userid) == 0:
			return render_template('index.html', status="badUserID")
		elif badChars.search(userid) != None:
			return  render_template('index.html', status="badCharsInUserID")
		elif age == None:
			return  render_template('index.html', status="badAge")
		
		firstNumber = random.randint(1000,5000)
		secondNumber = random.randint(6000,9000)

		generate = zlib.adler32(str(str(secondNumber) + userid + str(firstNumber)).encode())

		openDatabase.execute("""INSERT INTO users
			               (userID, KnowBe4Score, gender, education, age) VALUES (?, ?, ?, ?, ?)""",
			                (generate, knownBe4Number, gender, educationLevel, age))
		database.commit()
		session['userid'] = generate
		database.close()
		return redirect('startScreen')	
	return render_template('index.html')

@app.route("/startScreen", methods=['GET', 'POST'])
def startScreen():
	return render_template('startScreen.html', userid=session['userid'])

@app.route("/Behavioral", methods=['GET', 'POST'])
def Behavioral():
	if request.method == 'POST':
		session['temp']  = 0
		for x in range(0,len(session['behavioralQuestions'])):
			writeToBehavioralDB(str(x+1), int(request.form['question-'+str(x)+'-answers']), session['userid'])
			session['temp']  = session['temp']  + int(request.form['question-'+str(x)+'-answers'])
			session['BehavioralTotalAnswer'] = session['temp'] 

		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()
		openDatabase.execute("UPDATE users SET DH = ? WHERE userid=?",(session['BehavioralTotalAnswer'], session['userid']))
		database.commit()
		database.close()

		return redirect(url_for("SocialMedia"))
	if request.method == 'GET':
		session['behavioralQuestions'] = []
		session['behavioralAnswers'] = []
		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()
		openDatabase.execute("""SELECT question FROM behaviorQuestionsAndAnswers 
				                """)
		rows = openDatabase.fetchall()

		for row in rows:
			session['behavioralQuestions'].append(''.join(row))
			
		#randomize the questions
		database.close()	 	
		return render_template('Behavioral.html', questions=session['behavioralQuestions'], numberOfQuestions=len(session['behavioralQuestions']))

@app.route("/SocialMedia", methods=['GET', 'POST'])
def SocialMedia():
	if request.method == 'POST':
		session['temp'] = 0
		for x in range(0,27):
			writeToSocialDB(str(x+1), int(request.form['question-'+str(x)+'-answers']), session['userid'])
			session['temp']  = session['temp']  + int(request.form['question-'+str(x)+'-answers'])
			session['SocialMediaTotalAnswer'] = session['temp']
		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()
		openDatabase.execute("UPDATE users SET SM = ? WHERE userid=?",(session['SocialMediaTotalAnswer'], session['userid']))
		database.commit()
		database.close()
		session['FirstCall'] = 'first'
		return redirect(url_for("Questions"))

	if request.method == 'GET':		
		session['socialMediaQuestions'] = []
		session['socialMediaAnswers'] = []
		session['numberOfAnswers'] = []
		session['socialMediaAnswerValues'] = []
		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()
		openDatabase.execute("SELECT question FROM socialMediaQuestionsAndAnswers")
		rows = openDatabase.fetchall()

		for row in rows:
			session['socialMediaQuestions'].append(''.join(row))

		#randomize the questions
		for x in session['socialMediaQuestions']:
			openDatabase.execute("SELECT answers FROM socialMediaQuestionsAndAnswers WHERE question=?",(x,))
			answer = openDatabase.fetchone()
			openDatabase.execute("SELECT numOfAnswers FROM socialMediaQuestionsAndAnswers WHERE question=?",(x,))
			numberOfAnswers = openDatabase.fetchone()
			openDatabase.execute("SELECT answerValues FROM socialMediaQuestionsAndAnswers WHERE question=?",(x,))
			answerValues = openDatabase.fetchone()
			session['numberOfAnswers'].append(int(''.join(numberOfAnswers)))
			session['socialMediaAnswers'].append(json.loads(''.join(answer)))
			session['socialMediaAnswerValues'].append(json.loads(''.join(answerValues)))

		database.close()
		return render_template('SocialMedia.html', questions=session['socialMediaQuestions'], numberOfQuestions=len(session['socialMediaQuestions']), answers=session['socialMediaAnswers'], numberOfAnswers=session['numberOfAnswers'], answerValues=session['socialMediaAnswerValues'])
'''
Broke when calculating X I need to change it so the perc
'''
@app.route("/Questions", methods=['GET', 'POST'])
def Questions():
	if session['FirstCall'] == 'first':
		tempUser = session['userid'] 
		session.clear()
		
		session['userid'] = tempUser
		session['timerDict'] = []
		session['percentageCorrect'] = 0.0
		session['TotalQuestionsCorrect'] = 0
		session['totalQuestionsAsked'] = 0
		session['Q_Level'] = 1
		session['Topic_Number'] = 1
		session['NumberofCorrect'] = 0
		session['XTotal'] = 0.0
		getQuestions(session['Topic_Number'], session['Q_Level'], 4)
		getAnswers(session['otherQuestions'])
		session['FirstCall'] = "No"

	if request.method == 'POST':
		
		session['totalQuestionsAsked'] = session['totalQuestionsAsked'] + 4
		timerDict = json.loads(request.form['timerDict'])
		
		for x in range(0, 4):
			session['timerDict'].append(timerDict['question-'+str(x)+'-timer'])
			checkAnswers(session['QuestionID'][x], request.form['question-'+str(x)+'-answers'])
		if session['NumberofCorrect'] != 4:
			session['Topic_Number'] = session['Topic_Number'] + 1
			session['percentageCorrect'] = (session['TotalQuestionsCorrect'] /  session['totalQuestionsAsked']) * 100
			addTimerAverageToDB(session['Topic_Number'] - 1, session['timerDict'], session['Q_Level'])
			session['Q_Level'] = 1
			session['NumberofCorrect'] = 0

		elif session['NumberofCorrect'] == 4:
			session['Q_Level'] = session['Q_Level'] + 1
			session['NumberofCorrect'] = 0
			session['percentageCorrect'] = (session['TotalQuestionsCorrect'] /  session['totalQuestionsAsked']) * 100

		if session['Q_Level'] == 5:
			
			session['percentageCorrect'] = (session['TotalQuestionsCorrect'] /  session['totalQuestionsAsked']) * 100
			addTimerAverageToDB(session['Topic_Number'], session['timerDict'], session['Q_Level'])
			session['Q_Level'] = 1
			session['Topic_Number'] = session['Topic_Number'] + 1

		if session['Topic_Number'] == 8:
			calculateSusceptibility()
			

			return redirect(url_for("results")) 
		getQuestions(session['Topic_Number'], session['Q_Level'], 4)
		getAnswers(session['otherQuestions'])
		return render_template('Questions.html', questions=session['otherQuestions'][0:4], numberOfQuestions=4, answers=session['otherQuestionsAnswers'], numberOfAnswers=4) 

	if request.method == 'GET':
		getQuestions(session['Topic_Number'], session['Q_Level'], 4)
		getAnswers(session['otherQuestions'])
		

		return render_template('Questions.html', questions=session['otherQuestions'][0:4], numberOfQuestions=4, answers=session['otherQuestionsAnswers'])

def getAnswers(questions):
	session['otherQuestionsAnswers'] = []
	database = sqlite3.connect('database.sqlite3')
	openDatabase = database.cursor()
	for question in questions:
		openDatabase.execute("SELECT answers FROM OtherQuestions WHERE question=?",(question,))
		answer = openDatabase.fetchone()
		answers = json.loads(''.join(answer))
		random.shuffle(answers)
		session['otherQuestionsAnswers'].append(answers)
	database.close()
	

def getQuestions(topicNumber, level, amount):
	session['otherQuestions'] = []
	session['QuestionID'] = []
	database = sqlite3.connect('database.sqlite3')
	openDatabase = database.cursor()
	openDatabase.execute("SELECT question, P_KEY FROM OtherQuestions WHERE Q_Level = ? AND Topic_Number = ?", (level, topicNumber,))
	rows = openDatabase.fetchall()
	numberOfQestionsInLevel = len(rows)
	database.close()
	
	random.shuffle(rows)
	
	for x in range(0,len(rows)):
		session['otherQuestions'].append(''.join(rows[x][0]))
		session['QuestionID'].append(rows[x][1])


def checkAnswers(questionID, givenAnswer):
	database = sqlite3.connect('database.sqlite3')
	openDatabase = database.cursor()
	openDatabase.execute("SELECT Answer_Correct FROM OtherQuestions WHERE P_KEY = ?", (questionID,))
	rows = openDatabase.fetchall()
	
	for row in rows:
		givenAnswer = givenAnswer.replace(" ", "")
		fromDB = ''.join(row).replace(" ", "")

		if(givenAnswer == fromDB):
			session['NumberofCorrect'] = session['NumberofCorrect'] + 1
			session['TotalQuestionsCorrect'] = session['TotalQuestionsCorrect'] + 1

def addTimerAverageToDB(topicNumber, timerArray, Q_Level):
	
	session['TotalQuestionsCorrect'] = 0
	session['totalQuestionsAsked'] = 0
	database = sqlite3.connect('database.sqlite3')
	openDatabase = database.cursor()
	session['average'] = sum(timerArray) / len(timerArray)
	if(topicNumber == 1):
		openDatabase.execute("UPDATE users SET TopicOneAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	elif(topicNumber == 2):
		openDatabase.execute("UPDATE users SET TopicTwoAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	elif(topicNumber == 3):
		openDatabase.execute("UPDATE users SET TopicThreeAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	elif(topicNumber == 4):
		openDatabase.execute("UPDATE users SET TopicFourAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	elif(topicNumber == 5):
		openDatabase.execute("UPDATE users SET TopicFiveAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	elif(topicNumber == 6):
		openDatabase.execute("UPDATE users SET TopicSixAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	elif(topicNumber == 7):
		openDatabase.execute("UPDATE users SET TopicSevenAverageTime = ? WHERE userid = ?", (session['average'], session['userid']))
	
	database.commit()
	database.close()
	calculateX(topicNumber, Q_Level)
def calculateX(topicNumber, Q_Level):
	session['X'] = (session['percentageCorrect']/session['average']) * session['Q_Level']
	session['XTotal'] = session['XTotal'] + session['X']
	database = sqlite3.connect('database.sqlite3')
	openDatabase = database.cursor()
	if(topicNumber == 1):
		openDatabase.execute("UPDATE users SET TopicOneX = ? WHERE userid = ?", (session['X'], session['userid']))
	elif(topicNumber == 2):
		openDatabase.execute("UPDATE users SET TopicTwoX = ? WHERE userid = ?", (session['X'], session['userid']))
	elif(topicNumber == 3):
		openDatabase.execute("UPDATE users SET TopicThreeX = ? WHERE userid = ?", (session['X'], session['userid']))
	elif(topicNumber == 4):
		openDatabase.execute("UPDATE users SET TopicFourX = ? WHERE userid = ?", (session['X'], session['userid']))
	elif(topicNumber == 5):
		openDatabase.execute("UPDATE users SET TopicFiveX = ? WHERE userid = ?", (session['X'], session['userid']))
	elif(topicNumber == 6):
		openDatabase.execute("UPDATE users SET TopicSixX = ? WHERE userid = ?", (session['X'], session['userid']))
	elif(topicNumber == 7):
		openDatabase.execute("UPDATE users SET TopicSevenX = ? WHERE userid = ?", (session['X'], session['userid']))
	database.commit()
	database.close()
	session['timerDict'] = []

def calculateSusceptibility():
	'''S = (XTotal/(Hb+SM))*1000
	cursor.fetchone
	'''
	database = sqlite3.connect('database.sqlite3')
	openDatabase = database.cursor()
	openDatabase.execute("SELECT DH FROM users WHERE userid = ?", (session['userid'],))
	session['Hb'] = openDatabase.fetchone()
	session['Hb']  = functools.reduce(lambda sub, ele: sub * 10 + ele, session['Hb']) 
	openDatabase.execute("SELECT SM FROM users WHERE userid = ?", (session['userid'],))
	session['SM'] = openDatabase.fetchone()
	session['SM']  = functools.reduce(lambda sub, ele: sub * 10 + ele, session['SM']) 
	session['Susceptibility'] = (session['XTotal']/(int(session['Hb'])+int(session['SM'])))*1000
	openDatabase.execute("UPDATE users SET Susceptibility = ? WHERE userid = ?", (session['Susceptibility'], session['userid']))
	database.commit()
	database.close()
	

@app.route("/results", methods=['GET', 'POST'])
def results():
	return render_template("results.html", Susceptibility=session['Susceptibility'], userid=session['userid'])


def writeToBehavioralDB(questionNumber, value, userid):
		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()
		openDatabase.execute("""INSERT INTO behavioralQuestionsResponses
			               (userID, questionNumber, score) VALUES (?, ?, ?)""",
			                (userid, questionNumber, value))
		database.commit()
		database.close()

def writeToSocialDB(questionNumber, value, userid):
		database = sqlite3.connect('database.sqlite3')
		openDatabase = database.cursor()
		openDatabase.execute("""INSERT INTO socialQuestionsResponses
			               (userID, questionNumber, score) VALUES (?, ?, ?)""",
			                (userid, questionNumber, value))
		database.commit()
		database.close()

if __name__ == "__main__":
	#app.run(host='192.168.82.199')
	serve(app, port=5000)
