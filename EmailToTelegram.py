import imaplib
import email
import os
import magic  # python-magic library
import asyncio
import logging

from telegram import Bot

# Gmail account credentials
EMAIL = 'email account username'
PASSWORD = 'email account password'

# Telegram bot credentials
TELEGRAM_TOKEN = 'your Telegram Bot token'
TELEGRAM_CHAT_ID = 'Chat Id where to send pics'

# Folder or label name to search for
#FOLDER_LABEL_NAME = 'INBOX'
logging.basicConfig(level=logging.WARN)


# Function for sending messages
async def send_telegram_message(text):
    bot = Bot(TELEGRAM_TOKEN)
    await bot.send_message(TELEGRAM_CHAT_ID, text)

# Function for sending images
async def send_image_to_telegram(filepath):
    try:
        with open(filepath, 'rb') as f:
            #await send_telegram_message("Sending image...")
            bot = Bot(TELEGRAM_TOKEN)
            await bot.send_photo(TELEGRAM_CHAT_ID, f)
    except Exception as e:
        print(f"Failed to send photo: {e}")
        logging.error(f"Failed to send photo: {e}")

async def process_emails():
    # Connect to Gmail IMAP server
    imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_server.login(EMAIL, PASSWORD)
    imap_server.select('INBOX')  # Select the desired folder/label

    # Create a magic instance for file type detection
    mime = magic.Magic()
#    logging.info("Starting processing emails...")
    # Search for all emails in the selected folder/label
    status, messages = imap_server.search(None, 'UNSEEN', 'OR (FROM "burrelhunting.com") (FROM "reolink@halkosaari.fi")')

    if status == 'OK':
        num_emails = len(messages[0].split())

#        if num_emails == 0:
#           logging.info("no emails")

        for msg_id in messages[0].split():
            _, msg_data = imap_server.fetch(msg_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Log email subject and sender
                    email_subject = msg.get("Subject")
                    email_sender = msg.get("From")
                    print(f"Email Subject: {email_subject}")
                    print(f"Email Sender: {email_sender}")

                    # Download image attachments
                    num_images = 0
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        filename = part.get_filename()

                        if content_type == 'image/jpeg' or (filename and filename.lower().endswith('.jpg')):
                            num_images += 1
                            filepath = os.path.join('/home/users/antha/EmailToTelegram/images', filename)
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))

                            # Send images to Telegram chat
                            await send_image_to_telegram(filepath)
                            logging.info("Message sent to telegram")

                            # Remove image file from disk
                            os.remove(filepath)

                    if num_images > 0:
                        text = f"Processed {num_images} images from {num_emails} email(s) in the INBOX folder/label."
                        await send_telegram_message(text)
                        logging.info("Text message sent to telegram")


                    # Move the email to the Trash folder
                    imap_server.store(msg_id, '+X-GM-LABELS', '\\Trash')

    # Close the connection to the Gmail server
    imap_server.expunge()
    imap_server.close()
    imap_server.logout()

if __name__ == "__main__":
    asyncio.run(process_emails())

