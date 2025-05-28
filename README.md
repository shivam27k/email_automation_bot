# 📧 Email Sender Bot with Threading Support

Must read the [NOTE](#note) section at the bottom of this file.

⭐ Star this project if you find it useful!🔗 Feel free to connect with me on LinkedIn at [shivam-27k](https://www.linkedin.com/in/shivam-27k) >\_<.

## 🧐 Overview

This Python-based Email Sender Bot automates sending personalized emails to multiple recipients from a CSV file. It customizes each email with the recipient’s name, job role, and company name — and attaches a PDF resume.

Now enhanced with multi-threading for faster delivery — with user-controlled thread count and built-in safety warnings to help you stay under Gmail’s sending limits.

## ✨ Features

-   ✅ Read recipient info from a CSV file

-   ✅ Customize subject and body using dynamic recipient info

-   ✅ Attach resume (PDF) automatically

-   ✅ Secure SMTP login with Gmail App Password

-   ✅ Multi-threaded sending for better speed

-   ✅ User-defined thread count (max 5 threads)

-   ✅ Built-in delay & throttling to avoid Gmail spam filters

-   ✅ Displays warnings about Gmail sending limits

# ⚙️ How to Use

#### 1. ✅ Prerequisites

Install Python 3.x from the official site (Google it if needed).

Make sure you're in the root directory of this project.

#### 2. 📦 Install Dependencies

```
pip install -r requirements.txt
```

#### 3. 📄 Replace Example Files

Replace `example.csv` with your own recipient list.The CSV file must include the following headers:

`name,email,job_role,company_name`

Replace `example.pdf` with the file you want to attach in the mail.

#### 4. ⚙️ Configure Your Email Settings

Open config.py and edit these values:

```
SENDER_NAME = "Your Name"
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # See NOTE below
FILE_PATH = "path/to/your_resume.pdf"
CSV_FILE_PATH = "path/to/your_recipients.csv"
```

#### 5. 🚀 Run the Bot

```
python email_sender.py
```

You’ll be shown a Gmail safety warning and then prompted to enter how many threads you want to use (between 1–5). The more threads, the faster the process — but higher the risk of getting flagged by Gmail.

⚠️ Gmail Safety Guidelines

When sending emails via Gmail SMTP, keep the following in mind:

📬 Normal Gmail accounts support 100–150 emails/day max.

⛔ Don't send too many at once (20–30 per batch is safe).

🚨 More than 5 threads or spamming too fast can get your account flagged or suspended.

✅ Use randomized delays and respect sending intervals.

🧐 If you're unsure, use 1–2 threads and space out large sends.

## NOTE

Your Gmail `SENDER_PASSWORD` is NOT your normal password. You must generate an `App Password` by following these steps:

#### Follow these steps to enable 2-factor authentication:

1. Open your [Google Account](https://myaccount.google.com/).
2. In the navigation panel, select "Security".
3. Under “How you sign in to Google,” select Turn on 2-Step Verification.
4. Follow the on-screen steps.

#### Generate your app password

1. You must generate an `App Password` using this link: [Google App Password Generator](https://myaccount.google.com/apppasswords).

2. Copy the 16-digit password and paste it in config.py under SENDER_PASSWORD.

## 📬 Output Example

Each recipient gets a custom email like this:

Hi John,

I hope you're doing well.I am writing to express my interest in the Software Engineer position at Acme Corp...

[Your resume will be attached]

## ✅ Final Tips

Always test by sending it to your own email first.

Start with 1–2 threads to warm up.

Update the email content inside the generate_email_content() function in email_utils.py.

📸 Result Preview

![Example image of the email sent](example.jpg)

Happy mailing! 📨
