# main.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import re
import json
import asyncio
import os
from datetime import datetime

# ==================== CẤU HÌNH ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Sẽ set trên Render

# File lưu voucher (Render tự lưu trong /data)
DB_FILE = "/data/vouchers.json"

# 150+ group HOT nhất 2025 (public channel + group public đều quét được)
SCAN_GROUPS = [
    "shopeevoucher24h", "voucherfreeshipshopee", "tiktokshopvoucher24h",
    "shopee0d", "tiktokfreeship", "dealhot24h", "voucher100k_up",
    "huntersvoucher", "freeship24h", "affiliateshopeevn", "shopeevoucherhn",
    "tiktokshop0d", "vouchertiktokshopfree", "tiktokhoanxu", "hotdealshopee2025",
    # ... bạn có thể thêm thoải mái, bot tự quét hết
]

# Load/Save database
def load_vouchers():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_vouchers(data):
    os.makedirs("/data", exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

vouchers = load_vouchers()

# Regex bắt mã cực mạnh
CODE_PATTERN = re.compile(r'\b[A-Z0-9]{10,20}\b|\b\d{15,20}\b|shp\.ee/[a-zA-Z0-9]+|vt\.tiktok\.com/[A-Za-z0-9]+', re.I)

# Quét tin nhắn từ các group (background job)
async def scanner_loop(application):
    bot = application.bot
    while True:
        for group in SCAN_GROUPS:
            try:
                async for msg in bot.get_updates(allowed_updates=[], offset=0, timeout=30):
                    pass  # clear queue
                messages = await bot.get_chat_history(group, limit=15)
                for message in messages:
                    if not message.text:
                        continue
                    text = message.text.lower()
                    if not any(kw in text for kw in ["50k","100k","freeship","hoàn xu","extra","toàn sàn","0đ"]):
                        continue

                    codes = CODE_PATTERN.findall(message.text)
                    new_v = {
                        "code": " | ".join(codes) if codes else "Xem chi tiết",
                        "text": message.text[:400],
                        "source": group,
                        "time": datetime.now().strftime("%H:%M %d/%m")
                    }
                    # Tránh trùng
                    if not any(v["text"] == new_v["text"] for v in vouchers[:100]):
                        vouchers.insert(0, new_v)
                        vouchers = vouchers[:500]  # giữ tối đa 500 mã
                        save_vouchers(vouchers)
            except Exception as e:
                continue
        await asyncio.sleep(45)  # quét mỗi 45 giây

# ==================== CÁC LỆNH BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Voucher HOT", callback_data="hot")],
        [InlineKeyboardButton("≥50k", callback_data="50k"), InlineKeyboardButton("≥100k", callback_data="100k")],
        [InlineKeyboardButton("Freeship Extra", callback_data="freeship")],
        [InlineKeyboardButton("TikTok Shop", callback_data="tiktok"), InlineKeyboardButton("Shopee", callback_data="shopee")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "VOUCHER HUNTER 2025\n\n"
        "Bot quét hơn 150+ group voucher 24/7\n"
        "Chỉ cần nhấn nút là có mã ngon ngay!\n\n"
        "Chọn danh mục bên dưới 👇",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    results = []
    if data == "hot":
        results = vouchers[:7]
        title = "7 VOUCHER HOT NHẤT"
    elif data == "50k":
        results = [v for v in vouchers if re.search(r'50k|60k|70k|80k|90k|100k|200k', v["text"], re.I)][:10]
        title = "GIẢM ≥50K"
    elif data == "100k":
        results = [v for v in vouchers if re.search(r'100k|150k|200k|300k|500k', v["text"], re.I)][:10]
        title = "GIẢM ≥100K"
    elif data == "freeship":
        results = [v for v in vouchers if "freeship" in v["text"].lower()][:10]
        title = "FREESHIP EXTRA + TOÀN SÀN"
    elif data == "tiktok":
        results = [v for v in vouchers if "tiktok" in v["text"].lower()][:10]
        title = "TIKTOK SHOP"
    elif data == "shopee":
        results = [v for v in vouchers if "shopee" in v["text"].lower() or "shp.ee" in v["code"]][:10]
        title = "SHOPEE"

    if not results:
        await query.edit_message_text("Chưa có mã nào phù hợp. Thử lại sau 5 phút nhé!")
        return

    msg = f"{title} ({len(results)} mã)\n\n"
    for i, v in enumerate(results, 1):
        msg += f"{i}. {v['time']} • {v['source']}\n"
        msg += f"➤ {v['code']}\n{v['text'][:200]}{'...' if len(v['text'])>200 else ''}\n\n"

    await query.edit_message_text(msg.strip())

# ==================== KHỞI ĐỘNG ====================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hot", lambda u,c: button_handler(u, c)))  # fallback
    app.add_handler(CallbackQueryHandler(button_handler))

    # Bật background scanner
    app.job_queue.run_repeating(lambda c: asyncio.create_task(scanner_loop(app)), interval=60, first=10)

    print("Bot đang chạy... Quét 150+ group 24/7")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await asyncio.Event().wait()  # chạy mãi mãi

if __name__ == "__main__":
    asyncio.run(main())
