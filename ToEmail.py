import smtplib
import os


def send_notification(subject: str, body: str, from_email: str, to_email: str) -> bool:
    with smtplib.SMTP("smtp.gmail.com") as connection:
        message = "Subject:" + subject + "\n\n" + body
        connection.starttls()
        connection.login(user=from_email, password=os.environ["GMAIL_PASSWORD"])
        response = connection.sendmail(from_addr=from_email, to_addrs=to_email, msg=message)
        print(response)
    return True

