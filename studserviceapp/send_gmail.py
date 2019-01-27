import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
import os
from apiclient import errors, discovery
import oauth2client
from oauth2client import client, tools, file
import httplib2
import email.encoders
from email.header import Header
from email.utils import formataddr
from django.conf import settings

try:
    import argparse
    flags = tools.argparser.parse_args([])
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Studentski Servis - Jev'
emailaddress = "jmarkovic16@raf.rs"


def get_credentials():
    credential_dir = settings.BASE_DIR
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-api.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials


def create_message(header_text, sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """

  author = formataddr((str(Header(header_text, 'utf-8')), emailaddress))
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = author

  message['subject'] = subject 
  
  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def create_message_with_attachment(header_text,
    sender, to, subject, message_text, file):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.
    file: The path to the file to be attached.

  Returns:
    An object containing a base64url encoded email object.
  """
  author = formataddr((str(Header(header_text, 'utf-8')), emailaddress))
  message = MIMEMultipart()
  
  message['to'] = to
  message['from'] = author
  message['subject'] = subject

  msg = MIMEText(message_text)
  message.attach(msg)

  content_type, encoding = mimetypes.guess_type(file)

  if content_type is None or encoding is not None:
    content_type = 'application/octet-stream'
  main_type, sub_type = content_type.split('/', 1)
  if main_type == 'text':
    fp = open(file, 'rb')
    msg = MIMEText(fp.read(), _subtype=sub_type)
    fp.close()
  elif main_type == 'image':
    fp = open(file, 'rb')
    msg = MIMEImage(fp.read(), _subtype=sub_type)
    fp.close()
  elif main_type == 'audio':
    fp = open(file, 'rb')
    msg = MIMEAudio(fp.read(), _subtype=sub_type)
    fp.close()
  else:
    fp = open(file, 'rb')
    msg = MIMEBase(main_type, sub_type)
    msg.set_payload(fp.read())
    fp.close()
  filename = os.path.basename(file)
  msg.add_header('Content-Disposition', 'attachment', filename=filename)
  message.attach(msg)

  return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
     print('An error occurred: %s' % error)



def create_and_send_message(header_text, sender, to, subject, msgPlain, attachmentFile=None):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    if attachmentFile:
        message1 = create_message_with_attachment(header_text, sender, to, subject, msgPlain, attachmentFile)
    else:
        message1 = create_message(header_text, sender, to, subject, msgPlain)
    result = send_message(service, emailaddress, message1)
    return result










