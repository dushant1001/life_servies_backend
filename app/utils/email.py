import smtplib
from email.mime.text import MIMEText

EMAIL = "kdushant8899@gmail.com"
PASSWORD = "ontqsxtwhjzfhsah"




def send_otp_email(to_email: str, otp: str):

    subject = "Password Reset OTP"
    body = f"Your OTP is: {otp}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)

    server.sendmail(EMAIL, to_email, msg.as_string())
    server.quit()