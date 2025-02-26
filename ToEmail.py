import smtplib
import os
import requests



def send_notification(subject: str, body: str, from_email: str, to_email: str) -> str:
	message=requests.post(
		"https://api.mailgun.net/v3/sandbox57bbca6e8fa04dbf881d5afcb0f1aa54.mailgun.org/messages",
		auth=("api", os.environ.get("PRIVATE_API_KEY")),
		data={"from": from_email,
			"to": to_email,
			"subject": subject,
			"text": body})
	#print(message.text)
	return message.text

# You can see a record of this email in your logs: https://app.mailgun.com/app/logs.

# You can send up to 300 emails/day from this sandbox server.
# Next, you should add your own domain so you can send 10000 emails/month for free.
