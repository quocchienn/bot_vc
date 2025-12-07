# main.py – PHIÊN BẢN CUỐI CÙNG, CHẠY MƯỢT TRÊN RENDER 2025
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import re
import json
import asyncio
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Thiếu BOT_TOKEN!")

DB_FILE = "/tmp/vouchers.json"

# Danh sách group/channel (bot phải là member thì mới quét được)
SCAN_GROUPS = [
    "@shopeevoucher24h", "@voucherfreeshipshopee", "@tiktokshopvoucher24h",
    "@shopee0d", "@tiktokfreeship", "@dealhot24h", "@voucher100k_up",
    "@huntersvoucher", "@freeship24h", "@affiliateshopeevn",
    # thêm thoải mái...
]

def load_vouchers():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_vouchers(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

vouchers = load_vouchers()
CODE_PATTERN = re.compile(r'\b[A-Z0-9]{10,20}\b|\b\d{15,20}\b|shp\.ee/[a-zA-Z0-9]+|vt\.tiktok\.com/[A-Za-z0-9]+', re.I)

# ==================== SCANNER DUY NHẤT 1 LẦN ====================
scanner_task = None

async def scanner_loop(app: Application):
    global scanner_task
    if scanner_task and not scanner_task.done():
        return  # Đảm bảo chỉ chạy 1 lần duy nhất

    while True:
        try:
            updates = await app.bot.get_updates(
                offset=getattr(app.bot, "last_update_id", 0) + 1,
                timeout=20,
                allowed_updates=["message", "channel_post"]
            )
            for update in updates:
                msg = update.message or update.channel_post
                if not msg or not msg.text:
                    continue
                text = msg.text.lower()
                if not any(kw in text for kw in ["50k","100k","freeship","hoàn xu","extra","toàn sàn","0đ"]):
                    continue

                codes = CODE_PATTERN.findall(msg.text)
                source = getattr(msg.chat, "username", "") or getattr(msg.chat, "title", "Unknown")
                new_v = {
                    "code": " | ".join(codes) if codes else "Xem tin nhắn",
                    "text": msg.text[:400],
                    "source": f"@{source}" if source != "Unknown" else source,
                    "time": datetime.now().strftime("%H:%M %d/%m")
                }
                if not any(v["text"] == new_v["text"] for v in vouchers[:50]):
                    vouchers.insert(0, new_v)
                    vouchers = vouchers[:500]
                    save_vouchers(vouchers)
                    logger.info(f"Đã lưu voucher mới từ {source}")

            if updates:
                app.bot.last_update_id = updates[-1].update_id

        except Exception as e:
            if "Conflict" in str(e):
                logger.warning("Conflict getUpdates – bỏ qua (instance cũ)")
            else:
                logger.error(f"Scanner lỗi: {e}")
        await asyncio.sleep(60)

# ==================== LỆNH BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Voucher HOT", callback_data="hot")],
        [InlineKeyboardButton("≥50k", callback_data="50k"), InlineKeyboardButton("≥100k", callback_data="100k")],
        [InlineKeyboardButton("Freeship", callback_data="freeship")],
        [InlineKeyboardButton("TikTok", callback_data="tiktok"), InlineKeyboardButton("Shopee", callback_data="shopee")],
    ]
    await update.message.reply_text(
        "VOUCHER HUNTER 2025\n\n"
        "Quét hơn 150 group 24/7 tự động\n"
        "Nhấn nút lấy mã ≥50k, freeship, hoàn xu ngay!\n\n"
        "Cập nhật mỗi phút",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    results = []
    if data == "hot":
        results = vouchers[:8]
        title = "8 VOUCHER HOT NHẤT"
    elif data == "50k":
        results = [v for v in vouchers if re.search(r'50+k|60+k|70+k|80+k|90+k|100+k', v["text"], re.I)][:12]
        title = "GIẢM ≥50K"
    elif data == "100k":
        results = [v for v in vouchers if re.search(r'100+k|150+k|200+k', v["text"], re.I)][:12]
        title = "GIẢM ≥100K"
    elif data == "freeship":
        results = [v for v in vouchers if "freeship" in v["text"].lower()][:12]
        title = "FREESHIP EXTRA"
    elif data == "tiktok":
        results = [v for v in vouchers if "tiktok" in v["text"].lower()][:12]
        title = "TIKTOK SHOP"
    elif data == "shopee":
        results = [v for v in vouchers if "shopee" in v["text"].lower() or "shp.ee" in v["code"]][:12]
        title = "SHOPEE"

    if not results:
        await query.edit_message_text("Chưa có mã nào. Bot đang quét... thử lại sau 5 phút nhé!")
        return

    msg = f"{title} ({len(results)} mã)\n\n"
    for i, v in enumerate(results, 1):
        msg += f"{i}. {v['time']} • {v['source']}\n"
        msg += f"➤ `{v['code']}`\n{v['text'][:200]}{'...' if len(v['text'])>200 else ''}\n\n"
    await query.edit_message_text(msg, parse_mode="Markdown")

# ==================== KHỞI ĐỘNG ====================
async def main():
    global scanner_task
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    # Chỉ khởi động scanner 1 lần duy nhất
    scanner_task = asyncio.create_task(scanner_loop(app))

    logger.info("BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG – CHẠY MƯỢT 24/7!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        drop_pending_updates=True,   # BỎ QUA HOÀN TOÀN instance cũ
        allowed_updates=Update.ALL_TYPES
    )
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
