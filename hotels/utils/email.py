import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


def send_email(title, output_file):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('draganaasd@gmail.com', 'fppvxeifuipjwlyg')

    # msg = EmailMessage()
    # msg.add_header('Content-Type', 'text/html')
    # msg.set_payload(email_html(data))
    # msg.set_charset('utf-8')

    msg = MIMEMultipart()
    msg['Subject'] = title
    msg['From'] = 'draganaasd@gmail.com'
    msg['To'] = 'dragana.grbic@dunavnet.eu'

    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(output_file, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(output_file))
    msg.attach(part)

    server.send_message(msg)
    server.quit()
