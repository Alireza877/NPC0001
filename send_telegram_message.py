
import os
import requests
import sys

# Get secrets from environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
MESSAGES_FILE = 'messages.txt'

def send_message(chat_id, text):
    """Sends a message to a specified Telegram chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Return a dictionary with the error to be handled by the main logic
        return {'ok': False, 'error_code': 'RequestException', 'description': str(e)}

def main():
    """Main function to run the script."""
    # Check if all required environment variables are set
    if not all([BOT_TOKEN, CHANNEL_ID, ADMIN_ID]):
        print("Error: One or more required environment variables are not set.", file=sys.stderr)
        # Cannot notify admin if secrets are missing, so just exit
        sys.exit(1)

    # Check if the messages file exists
    if not os.path.isfile(MESSAGES_FILE):
        error_text = f"فایل `{MESSAGES_FILE}` یافت نشد. ربات متوقف شد."
        send_message(ADMIN_ID, error_text)
        print(f"Error: {MESSAGES_FILE} not found. Notified admin.", file=sys.stderr)
        sys.exit(1)

    # Read all lines from the message file
    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        error_text = f"خطا در خواندن فایل `{MESSAGES_FILE}`.\n\n*جزئیات فنی:*\n`{e}`"
        send_message(ADMIN_ID, error_text)
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # If the file is empty, notify the admin and exit gracefully
    if not lines:
        empty_message = f"فایل `{MESSAGES_FILE}` خالی است. هیچ پیامی برای ارسال در این نوبت وجود ندارد."
        send_message(ADMIN_ID, empty_message)
        print("Info: messages.txt is empty. Notified admin.")
        sys.exit(0)

    # Get the first line and prepare the rest
    message_to_send = lines[0].strip()
    remaining_lines = lines[1:]

    # If the line is empty after stripping, remove it and exit
    if not message_to_send:
        print("Info: First line is empty, removing it.")
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            f.writelines(remaining_lines)
        sys.exit(0)

    # Attempt to send the message to the channel
    print(f"Attempting to send message to channel {CHANNEL_ID}...")
    result = send_message(CHANNEL_ID, message_to_send)

    if result.get('ok'):
        print("Message sent successfully to the channel.")
        # Write the remaining lines back to the file
        try:
            with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
                f.writelines(remaining_lines)
            print(f"Successfully removed the sent message from {MESSAGES_FILE}.")
        except Exception as e:
            error_text = (f"پیام با موفقیت به کانال ارسال شد، اما در به‌روزرسانی فایل `{MESSAGES_FILE}` خطایی رخ داد. "
                          f"لطفاً فایل را به صورت دستی بررسی کنید تا از ارسال پیام تکراری جلوگیری شود.\n\n"
                          f"*جزئیات فنی:*\n`{e}`")
            send_message(ADMIN_ID, error_text)
            print(f"Error writing to file after sending: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # If sending failed, notify the admin and keep the message in the file
        print("Failed to send message to the channel.", file=sys.stderr)
        error_description = result.get('description', 'No description provided.')

        admin_error_message = (
            f"⚠️ *خطا در ارسال پیام به کانال تلگرام*\n\n"
            f"ربات نتوانست پیام را ارسال کند. این پیام در فایل باقی می‌ماند تا در نوبت بعدی مجدداً برای ارسال آن تلاش شود.\n\n"
            f"**متن پیام:**\n`{message_to_send}`\n\n"
            f"-----------------------------------\n"
            f"*جزئیات فنی خطا:*\n"
            f"```{error_description}```"
        )
        send_message(ADMIN_ID, admin_error_message)
        print(f"Error details sent to admin {ADMIN_ID}.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
