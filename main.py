# main.py
import os
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ────────────────────────────────────────────────
#                  配置区（只改这里）
# ────────────────────────────────────────────────
BOT_TOKEN = "8045586433:AAEIyz7e-cX9Ux6CrFEoMsEvnHRkMi7Pqzs"  # ← 改成新 Token！！！

BASE_IMAGE_PATH    = "images/base.png"
BATTERY_DIR        = "images"
FONT_PATH          = "arial.ttf"               # 没有就用系统默认或放一个 ttf 文件
DEFAULT_FONT_SIZE  = 48

# 坐标（以你的模板为准，左上角 0,0）
POS_TIME     = (189,  39)
POS_AMOUNT   = (687,  490)
POS_USD      = (637,  571)
POS_ADDRESS  = (837,  1146)
POS_BATTERY  = (1077, 35)

# 颜色（RGB）
COLOR_TEXT   = (255, 255, 255)   # 大部分 OKX 界面是白色

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_battery(percent: int) -> Image.Image:
    level = max(1, min(10, (percent + 5) // 10))  # 1→10%, 10→100%
    path = os.path.join(BATTERY_DIR, f"battery_{level}.png")
    if not os.path.exists(path):
        path = os.path.join(BATTERY_DIR, "battery_10.png")  # fallback
    img = Image.open(path).convert("RGBA")
    # 可选：统一大小（根据你的图标实际大小调整）
    # img = img.resize((68, 32), Image.Resampling.LANCZOS)
    return img

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "OKX Withdrawal Proof Generator (English)\n\n"
        "Send in this format (comma separated):\n"
        "amount, address, time, battery%\n\n"
        "Examples:\n"
        "• 1250, TAbc123xyz..., 14:35, 75\n"
        "• 500.8, TJ3bjc7HdgagxuUR3Z1A7m1g4bnuyWHYDp, 09:12, 30\n\n"
        "Time format: hh:mm    Battery: 1–100"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if ',' not in text:
        return

    try:
        parts = [p.strip() for p in text.split(',', 3)]
        if len(parts) != 4:
            await update.message.reply_text("Need exactly 4 parts separated by comma.")
            return

        amount_str, address, time_str, bat_str = parts

        # 金额处理
        amount = float(amount_str)
        amount_display = f"{amount:g}"
        usd_display = f"~${amount:g}"

        # 时间简单校验
        h, m = time_str.split(':')
        if not (h.isdigit() and m.isdigit() and 0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("Invalid time format")

        # 电量
        battery_pct = int(bat_str)
        if not 1 <= battery_pct <= 100:
            raise ValueError("Battery must be 1–100")

       # 加载底图
# 加载底图
try:
    base = Image.open(BASE_IMAGE_PATH).convert("RGBA")
except Exception as e:
    raise FileNotFoundError(f"Cannot open base image: {BASE_IMAGE_PATH}") from e

draw = ImageDraw.Draw(base)  # 正确，只有这一行

# 尝试加载字体，失败用默认
# 加载底图
try:
    base = Image.open(BASE_IMAGE_PATH).convert("RGBA")
except Exception as e:
    raise FileNotFoundError(f"Cannot open base image: {BASE_IMAGE_PATH}") from e

draw = ImageDraw.Draw(base)  # 正确，只有这一行

# 尝试加载字体，失败用默认
try:
    font_big   = ImageFont.truetype(FONT_PATH, 52)
    font_med   = ImageFont.truetype(FONT_PATH, 38)
    font_small = ImageFont.truetype(FONT_PATH, 32)
    font_addr  = ImageFont.truetype(FONT_PATH, 28)
except Exception:
    font_big = font_med = font_small = font_addr = ImageFont.load_default()
    logger.warning("Custom font not found, using default")

# 写入文字
draw.text(POS_TIME, time_str, font=font_small, fill=COLOR_TEXT)

draw.text(POS_AMOUNT, amount_display, font=font_big, fill=COLOR_TEXT, anchor="mm")

draw.text(POS_USD, usd_display, font=font_med, fill=COLOR_TEXT, anchor="mm")

draw.text(POS_ADDRESS, address, font=font_addr, fill=COLOR_TEXT, anchor="mm")

# 贴电量图标
bat = load_battery(battery_pct)
base.paste(bat, POS_BATTERY, bat)

        # 保存临时文件
        filename = f"okx_{update.effective_user.id}_{int(datetime.now().timestamp())}.png"
        base.save(filename, "PNG")

        await update.message.reply_photo(
            photo=open(filename, "rb"),
            caption=f"Withdrawn {amount_display} USDT\n{address}"
        )

        os.remove(filename)

    except Exception as e:
        logger.error(e, exc_info=True)
        await update.message.reply_text(f"Error: {str(e)}\nPlease check format or values.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
