import os
import subprocess
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram import Update

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")

async def reducir_y_guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    video = None
    if update.message.video:
        video = update.message.video
    elif update.message.document and update.message.document.mime_type and "video" in update.message.document.mime_type:
        video = update.message.document

    if not video:
        return

    await update.message.reply_text("Recibí tu video. Reduciendo calidad y guardando en la nube...")

    try:
        archivo = await video.get_file()
        entrada = "entrada.mp4"
        salida = "salida.mp4"
        await archivo.download_to_drive(entrada)

        comando = [
            "ffmpeg", "-y",
            "-i", entrada,
            "-vf", "scale=480:-2",
            "-b:v", "500k",
            "-b:a", "64k",
            salida
        ]
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=600)

        if resultado.returncode != 0 or not os.path.exists(salida):
            await update.message.reply_text("Error al comprimir el video.")
            return

        with open(salida, "rb") as f:
            await context.bot.send_video(chat_id=CANAL_ID, video=f, caption="Video guardado en tu nube")

        await update.message.reply_text("¡Listo! El video comprimido se ha guardado en tu canal privado.")

    except subprocess.TimeoutExpired:
        await update.message.reply_text("El proceso tardó demasiado.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:300]}")
    finally:
        for f in ["entrada.mp4", "salida.mp4"]:
            if os.path.exists(f):
                os.remove(f)

def main():
    app = ApplicationBuilder().token(TOKEN).connect_timeout(30).read_timeout(30).build()
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, reducir_y_guardar))
    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
