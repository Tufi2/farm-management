from flask import Flask
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Print environment variables (without showing the actual password)
print(f"MAIL_USERNAME: {os.environ.get('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD: {'*' * len(os.environ.get('MAIL_PASSWORD', ''))}")
print(f"MAIL_DEFAULT_SENDER: {os.environ.get('MAIL_DEFAULT_SENDER')}")

# Mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

with app.app_context():
    try:
        msg = Message('Test Email',
                     recipients=[os.environ.get('MAIL_USERNAME')])
        msg.body = 'This is a test email from Flask-Mail'
        print("Attempting to send test email...")
        mail.send(msg)
        print("Test email sent successfully!")
    except Exception as e:
        print(f"Error sending test email: {str(e)}")