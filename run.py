from flask import Flask, request, Response, render_template
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse, Say
from twilio.jwt.taskrouter.capabilities import WorkerCapabilityToken
import json, requests, time, os

app = Flask(__name__)

# Authroization
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_TRIAL_NUMBER']
workspace_sid = os.environ['TWILIO_WORKSPACE_SID']
workflow_sid = os.environ['TWILIO_WORKFLOW_SID']
client = Client(account_sid, auth_token)

@app.route("/assignment_callback", methods=['GET', 'POST'])
def assignment_callback():
    """Respond to assignment callbacks and sends a text"""

    time.sleep(5) #simulates an agent being busy and then becoming available. Ideally this would happen before /assignment_callback

    attributes  = request.values.get('TaskAttributes')
    attributes_dict = json.loads(attributes)
    caller_number = attributes_dict['from']
    want_text = attributes_dict['want_text']

    if want_text == 'True' :
        message = client.messages \
                    .create(
                        body='An agent is joining your call!',
                        from_=twilio_number,
                        to=caller_number
                    )
        print(message.sid)

    ret = '{"instruction": "dequeue", "from":"+18179346117", "post_work_activity_sid":"WA7d979296fe69fc1ce8bbf0af46acec9b"}' # a verified phone number from your twilio account
    resp = Response(response=ret, status=200, mimetype='application/json')
    return resp

@app.route("/incoming-call.php", methods=['GET', 'POST'])
def incoming_call():
    """Respond to incoming requests."""

    resp = VoiceResponse()
    with resp.gather(numDigits=1, action="/enqueue_call", method="POST", timeout=3) as g:
        g.say("Hello! Noone is available to take your call just yet. Stay on the line and we'll send you a text once an agent is available.")
        g.say("If you'd prefer not to recevie a text, press 2.")

    resp.redirect('/enqueue_call', method='POST')

    return str(resp)


@app.route("/enqueue_call", methods=['GET', 'POST'])
def enqueue_call():
    digit_pressed = request.values.get('Digits')
    if digit_pressed == "2" :
        want_text = False
    else:
        want_text = True

    resp = VoiceResponse()
    enqueue = resp.enqueue(None, workflow_sid=workflow_sid)
    enqueue.task('{"want_text":"' + str(want_text) +'"}')
    resp.append(enqueue)

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)