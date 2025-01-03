import os,zipfile,asyncio,telebot
from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API,UseCurrentSession

try:
    with open('tgBotToken.txt', 'r') as f:
        API_TOKEN = f.read().strip()
except FileNotFoundError:
    print("Error: tgBotToken.txt not found")
    exit(1)

bot = telebot.TeleBot(API_TOKEN)

async def convert_session_to_tdata(session_file):
    try:
        client = TelegramClient(session_file)
        tdesk = await client.ToTDesktop(flag=UseCurrentSession)
        unique_folder = f"temp_tdata_{os.path.splitext(os.path.basename(session_file))[0]}"
        os.makedirs(unique_folder, exist_ok=True)
        tdesk.SaveTData(unique_folder)
        return unique_folder
    except Exception as e:
        return f"Помилка конвертації: {str(e)}"

def zip_tdata_folder(source_folder):
    try:
        if not os.path.exists('tdata'):
            os.makedirs('tdata')
        zip_filename = os.path.join('tdata', f"tdata_{os.path.basename(source_folder)}.zip")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('tdata', os.path.relpath(file_path, source_folder))
                    zipf.write(file_path, arcname)
        return zip_filename
    except Exception as e:
        return f"Помилка створення архіву: {str(e)}"

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Привіт, це бот-конвертер .session в tdata \n Якщо після завантаження вашої сесії бот видає помилку то ця сесія є неактивною")

@bot.message_handler(content_types=['document'])
def handle_session_file(message):
    try:
        if not message.document.file_name.endswith('.session'):
            bot.reply_to(message, "Будь ласка, надішліть файл з розширенням .session")
            return

        os.makedirs("temp", exist_ok=True)
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        session_file_path = os.path.join("temp", f"{message.document.file_id}.session")
        
        with open(session_file_path, 'wb') as f:
            f.write(downloaded_file)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        temp_tdata_folder = loop.run_until_complete(convert_session_to_tdata(session_file_path))
        
        if isinstance(temp_tdata_folder, str) and temp_tdata_folder.startswith("Помилка"):
            bot.reply_to(message, temp_tdata_folder)
            if os.path.exists(session_file_path):
                os.remove(session_file_path)
            return

        zip_file = zip_tdata_folder(temp_tdata_folder)
        
        if isinstance(zip_file, str) and zip_file.startswith("Помилка"):
            bot.reply_to(message, zip_file)
            if os.path.exists(session_file_path):
                os.remove(session_file_path)
            return

        with open(zip_file, 'rb') as zipf:
            bot.send_document(message.chat.id, zipf)

        if os.path.exists(session_file_path):
            os.remove(session_file_path)
        if os.path.exists(temp_tdata_folder):
            for root, dirs, files in os.walk(temp_tdata_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_tdata_folder)
            
    except Exception as e:
        bot.reply_to(message, f"Виникла помилка: {str(e)}")

while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"Bot polling error: {str(e)}")
        continue
