import os
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ===========================
# CONFIGURATION
# ===========================
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # <-- Yahan apna token daalo

# GoFile.io ka default server fetch karne ke liye
def get_server():
    try:
        r = requests.get("https://api.gofile.io/servers")
        if r.status_code == 200 and r.json()["status"] == "ok":
            return r.json()["data"]["servers"][0]["name"]
    except Exception as e:
        print("Server fetch error:", e)
    return "store1"  # fallback

# GoFile.io pe file upload karega
def upload_to_gofile(file_path):
    server = get_server()
    url = f"https://{server}.gofile.io/contents/uploadfile"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                return data["data"]["downloadPage"]
    except Exception as e:
        print("Upload error:", e)
    return None

# Telegram se file receive karne ka handler
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print(f"File received from {user.first_name} ({user.id})")

    await update.message.reply_text("📽️ Video mila! Ab GoFile.io pe upload kar raha hoon...")

    # Video info nikalo
    video = update.message.video
    if not video:
        await update.message.reply_text("❌ Sirf video files support hain.")
        return

    file_size = video.file_size
    if file_size > 2 * 1024 * 1024 * 1024:  # 2 GB limit (GoFile free limit)
        await update.message.reply_text("⚠️ File 2GB se bada hai. GoFile free version sirf 2GB tak allow karta hai.")
        return

    # File download karo (temporary location)
    try:
        new_file = await context.bot.get_file(video.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            await new_file.download_to_drive(tmp_file.name)
            temp_path = tmp_file.name

        # Upload to GoFile
        link = upload_to_gofile(temp_path)

        # Temporary file delete karo
        os.unlink(temp_path)

        if link:
            await update.message.reply_text(f"✅ Upload ho gaya!\n\n📥 Download Link:\n{link}")
        else:
            await update.message.reply_text("❌ Upload fail ho gaya. Kuch technical issue hai.")
    except Exception as e:
        print("Error:", e)
        await update.message.reply_text("❌ Kuch galat ho gaya. File dobara bhejo.")

# Main function
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    print("✅ GoFile Telegram Bot chalu ho gaya!")
    app.run_polling()
