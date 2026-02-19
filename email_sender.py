import smtplib
import threading
import time
import random
from queue import Empty, Queue
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
    USE_GEMINI,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TIMEOUT_SECONDS,
    GEMINI_TEMPERATURE,
    GEMINI_DEBUG,
    GEMINI_MAX_RETRIES,
    GEMINI_RETRY_BASE_SECONDS,
    GEMINI_RETRY_MAX_SECONDS,
    EMAIL_STYLE_GUIDE,
    SENDER_PROFILE,
    ENABLE_COMPANY_RESEARCH,
    COMPANY_RESEARCH_TIMEOUT_SECONDS,
    COMPANY_RESEARCH_MAX_CHARS,
    get_runtime_diagnostics,
)
from email_utils import read_csv, attach_file
from email_content_generator import EmailContentGenerator

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


def send_email(recipient, content_generator):
    name = recipient["name"]
    email = recipient["email"]
    job_role = recipient["job_role"]
    company_name = recipient["company_name"]

    msg = MIMEMultipart()
    subject, body = content_generator.generate(recipient)

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


def thread_worker(recipient_queue, content_generator):
    while True:
        try:
            recipient = recipient_queue.get_nowait()
        except Empty:
            return

        try:
            send_email(recipient, content_generator)
        finally:
            recipient_queue.task_done()


def main():
    diagnostics = get_runtime_diagnostics()
    print("\nConfig diagnostics:")
    print(f"- cwd: {diagnostics['cwd']}")
    print(f"- .env path: {diagnostics['env_file_path']}")
    print(f"- dotenv available: {diagnostics['dotenv_available']}")
    print(f"- .env exists: {diagnostics['dotenv_file_exists']}")
    print(f"- .env loaded: {diagnostics['dotenv_loaded']}")
    print(f"- GEMINI enabled: {diagnostics['gemini_enabled']}")
    print(f"- GEMINI_API_KEY present: {diagnostics['gemini_api_key_present']} (len={diagnostics['gemini_api_key_len']})")
    print(f"- SENDER_PASSWORD present: {diagnostics['sender_password_present']} (len={diagnostics['sender_password_len']})")

    recipients = read_csv(CSV_FILE_PATH)
    total = len(recipients)

    if total == 0:
        print("📭 No recipients found.")
        return

    safety_warning(total)
    thread_count = get_thread_count()

    content_generator = EmailContentGenerator(
        sender_name=SENDER_NAME,
        sender_profile=SENDER_PROFILE,
        style_guide=EMAIL_STYLE_GUIDE,
        use_gemini=USE_GEMINI,
        gemini_api_key=GEMINI_API_KEY,
        gemini_model=GEMINI_MODEL,
        gemini_temperature=GEMINI_TEMPERATURE,
        gemini_timeout_seconds=GEMINI_TIMEOUT_SECONDS,
        gemini_debug=GEMINI_DEBUG,
        gemini_max_retries=GEMINI_MAX_RETRIES,
        gemini_retry_base_seconds=GEMINI_RETRY_BASE_SECONDS,
        gemini_retry_max_seconds=GEMINI_RETRY_MAX_SECONDS,
        enable_company_research=ENABLE_COMPANY_RESEARCH,
        company_research_timeout_seconds=COMPANY_RESEARCH_TIMEOUT_SECONDS,
        company_research_max_chars=COMPANY_RESEARCH_MAX_CHARS,
    )

    threads = []
    recipient_queue = Queue()
    for recipient in recipients:
        recipient_queue.put(recipient)

    for _ in range(thread_count):
        t = threading.Thread(target=thread_worker, args=(recipient_queue, content_generator))
        t.start()
        threads.append(t)

    recipient_queue.join()

    for t in threads:
        t.join()

    print("\n🎉 All emails processed safely.")


if __name__ == "__main__":
    main()
