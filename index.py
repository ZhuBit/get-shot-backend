from flask import Flask, request, jsonify
import json
import time
import pymongo
from flask_mail import Mail, Message
from flask_cors import CORS
from bson import ObjectId
from dotenv import dotenv_values, load_dotenv
import os

load_dotenv()
config = dotenv_values(".env")


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['DEBUG'] = False
app.config['MAIL_SERVER']='smtp.mail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

DATABASE_URL = os.getenv('DATABASE_URL')

mail = Mail(app)
CORS(app)

@app.route('/editPatient', methods = ['POST'])
def editPatient():
    try:
        patient = json.loads(request.data)['patient']
        client = pymongo.MongoClient(DATABASE_URL)
        db = client.getshotdb

        db.patients.update_one({'_id': ObjectId(patient['_id'])},
                               { "$set": { 'status': patient['status'] } })
        if patient['status'] == 3:
            sendQuestionary(patient['email'])


        return jsonify({
            'status': '200',
            'response': 'Patient edited',
        })
    except Exception as e:
        print('API error:', e)

@app.route('/patients', methods = ['GET'])
def getPatients():
    try:
      print('Get All Patients')
      patients = getAllPatients()

      response = JSONEncoder().encode({
          'status': '200',
          'data': patients
      })

      return response

    except Exception as e:
        print('API error:', e)


@app.route('/postPatient', methods = ['POST'])
def postPatient():
    try:
        patient = dict(json.loads(request.data))['patient']
        patient['createdAt'] = time.time()

        response = addToDb(patient)

        msg = sendEmail(patient['email'])

        return jsonify({
            'status': '200',
            'response': 'Patient added',
            'msg': msg
        })
    except Exception as e:
        print('API error:', e)

def addToDb(patient):
    print("adding patient")
    client = pymongo.MongoClient(DATABASE_URL)
    db = client.getshotdb
    response = db.patients.insert(patient)
    return 'response'

def sendEmail(recipient):
    print(f'Sending email to {recipient}...')
    msg = Message("Get your shot",
                  recipients=[recipient])
    with open('appointment.json') as json_file:
        mail_response = json.load(json_file)
    msg.body = mail_response['message']
    mail.send(msg)


def sendQuestionary(recipient):
    print(f'Sending second email to {recipient}...')
    msg = Message("Get your shot",
                  recipients=[recipient])
    with open('revaccination.json') as json_file:
        mail_response = json.load(json_file)

    msg.body = mail_response['message']
    mail.send(msg)

def getAllPatients():
    client = pymongo.MongoClient(DATABASE_URL)
    db = client.getshotdb
    patients = []

    cursor = db.patients.find({})
    for document in cursor:
        patients.append(document)
    return patients

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)