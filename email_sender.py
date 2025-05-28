import smtplib
import threading
import time
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import (
    SMTP_SERVER,
    SMTP_PORT,
    SENDER_EMAIL,
    SENDER_PASSWORD,
    FILE_PATH,
    CSV_FILE_PATH,
    SENDER_NAME,
)
from email_utils import read_csv, generate_email_content, attach_file

MAX_THREADS = 5
MAX_EMAILS_PER_BATCH = 30


def safety_warning(total_recipients):
    print(f"""
⚠️ GMAIL SENDING WARNING ⚠️

You're about to send {total_recipients} emails.

🚫 Gmail Safe Limits:
  - 100 to 150 emails/day on a normal Gmail account
  - No more than 20 to 30 in short intervals
  - Using too many threads may trigger spam filters

💥 Risks of Violating Limits:
  - Account suspension or temp lock
  - Deliverability damage (emails marked as spam)
  - Delayed or bounced messages

✅ Safe Usage Tips:
  - Use up to {MAX_THREADS} threads max
  - Send 20 to 30 emails per batch
  - Let the tool handle delays between sends
""")


def get_thread_count():
    while True:
        try:
            user_input = input(f"\n🔧 How many threads do you want to use? (1-{MAX_THREADS}): ")
            count = int(user_input)
            if 1 <= count <= MAX_THREADS:
                return count
            else:
                print(f"Please enter a number between 1 and {MAX_THREADS}.")
        except ValueError:
            print("❌ Invalid input. Please enter a numeric value.")


def send_email(recipient):
    name = recipient["name"]
    email = recipient["email"]
    job_role = recipient["job_role"]
    company_name = recipient["company_name"]

    msg = MIMEMultipart()
    subject, body = generate_email_content(name, job_role, company_name, sender_name=SENDER_NAME)

    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = email
    msg["Subject"] = subject
    msg["Reply-To"] = SENDER_EMAIL
    msg["X-Priority"] = "3"
    msg.attach(MIMEText(body, "plain"))

    attach_file(msg, FILE_PATH)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        print(f"Sent to {name} ({email})")
    except Exception as e:
        print(f"Failed to send to {email}: {e}")

    time.sleep(random.uniform(2, 6))  # Random delay to mimic human behavior


def thread_worker(queue):
    while queue:
        recipient = queue.pop(0)
        send_email(recipient)


def main():
    recipients = read_csv(CSV_FILE_PATH)
    total = len(recipients)

    if total == 0:
        print("📭 No recipients found.")
        return

    safety_warning(total)
    thread_count = get_thread_count()

    threads = []
    recipient_queue = recipients.copy()

    for _ in range(thread_count):
        t = threading.Thread(target=thread_worker, args=(recipient_queue,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\n🎉 All emails processed safely.")


if __name__ == "__main__":
    main()
