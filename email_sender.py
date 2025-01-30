import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, FILE_PATH, CSV_FILE_PATH, SENDER_NAME
from email_utils import read_csv, generate_email_content, attach_file

def send_email(recipient):
    """Sends an email to the given recipient."""
    name, email, job_role, company_name = recipient["name"], recipient["email"], recipient["job_role"], recipient["company_name"]
    
    msg = MIMEMultipart()
    subject, body = generate_email_content(name, job_role, company_name)
    
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"  # Use sender name from config
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    attach_file(msg, FILE_PATH)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        print(f"Email sent to {name} ({email})")
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")

def main():
    """Reads recipient details and sends emails."""
    recipients = read_csv(CSV_FILE_PATH)
    if not recipients:
        print("No recipients found. Check your CSV file.")
        return

    for recipient in recipients:
        send_email(recipient)

if __name__ == "__main__":
    main()
