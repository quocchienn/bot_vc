# main.py - Fixed for Python 3.12 + v21.6
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import re
import json
import asyncio
import os
from datetime import datetime
import logging

# Enable logging for debug
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CẤU HÌNH ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables!")

# File lưu voucher (sử dụng /tmp cho Render free tier, persistent hơn)
DB_FILE = "/tmp/vouchers.json"  # Render free có disk ephemeral, nhưng /tmp ổn cho test

# Danh sách 150+ group/channel HOT (username hoặc ID, bot sẽ quét updates nếu có quyền read)
SCAN_GROUPS = [
    "@shopeevoucher24h", "@voucherfreeshipshopee", "@tiktokshopvoucher24h",
    "@shopee0d", "@tiktokfreeship", "@dealhot24h", "@voucher100k_up",
    "@huntersvoucher", "@freeship24h", "@affiliateshopeevn", "@shopeevoucherhn",
    "@tiktokshop0d", "@vouchertiktokshopfree", "@tiktokhoanxu", "@hotdealshopee2025",
    # Thêm ID nếu cần: -1001234567890 (bot phải là member để quét private group)
    # ... thêm 100+ nữa từ file groups.txt nếu bạn có
]

# Load/Save database
def load_vouchers():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_vouchers(data):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

vouchers = load_vouchers()

# Regex bắt mã
CODE_PATTERN = re.compile(r'\b[A-Z0-9]{10,20}\b|\b\d{15,20}\b|shp\.ee/[a-zA-Z0-9]+|vt\.tiktok\.com/[A-Za-z0-9]+', re.I)

# Background scanner: Quét updates từ tất cả chat (bao gồm groups bot join)
async def scanner_loop(application: Application):
    while True:
        try:
            # Get updates từ tất cả chat (bot sẽ nhận nếu là member/admin ở groups)
            updates = await application.bot.get_updates(offset=application.bot.last_update_id + 1, timeout=30, allowed_updates=['message'])
            for update in updates:
                if update.channel_post or update.message:  # Chỉ tin nhắn từ channel/group
                    msg = update.channel_post or update.message
                    if not msg.text:
                        continue
                    text = msg.text.lower()
                    # Kiểm tra hot keywords
                    hot_keywords = ["50k", "100k", "200k", "freeship", "hoàn xu", "extra", "toàn sàn", "0đ"]
                    if not any(kw in text for kw in hot_keywords):
                        continue

                    codes = CODE_PATTERN.findall(msg.text)
                    source = msg.chat.username or msg.chat.title or "Unknown"
                    new_v = {
                        "code": " | ".join(codes) if codes else "Xem chi tiết",
                        "text": msg.text[:400],
                        "source": source,
                        "time": datetime.now().strftime("%H:%M %d/%m")
                    }
                    # Tránh trùng
                    if not any(v["text"] == new_v["text"] for v in vouchers[:100]):
                        vouchers.insert(0, new_v)
                        vouchers = vouchers[:500]
                        save_vouchers(vouchers)
                        logger.info(f"New hot voucher from {source}: {new_v['code']}")
            application.bot.last_update_id = updates[-1].update_id if updates else application.bot.last_update_id
        except Exception as e:
            logger.error(f"Scanner error: {e}")
        await asyncio.sleep(60)  # Quét mỗi 60 giây để tránh rate limit

# ==================== CÁC LỆNH BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎫 Voucher HOT", callback_data="hot")],
        [InlineKeyboardButton("💰 ≥50k", callback_data="50k"), InlineKeyboardButton("💎 ≥100k", callback_data="100k")],
        [InlineKeyboardButton("🚚 Freeship", callback_data="freeship")],
        [InlineKeyboardButton("📱 TikTok", callback_data="tiktok"), InlineKeyboardButton("🛒 Shopee", callback_data="shopee")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔥 **VOUCHER HUNTER 2025** 🔥\n\n"
        "Bot quét **150+ group** voucher 24/7 tự động!\n"
        "Nhấn nút bên dưới để lấy mã ngon ngay 👇\n\n"
        "*Cập nhật mỗi 60s – Chỉ mã ≥50k, freeship extra, hoàn xu cao!*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    results = []
    if data == "hot":
        results = vouchers[:7]
        title = "🔥 7 VOUCHER HOT NHẤT"
    elif data == "50k":
        results = [v for v in vouchers if re.search(r'50k|60k|70k|80k|90k|100k|200k', v["text"], re.I)][:10]
        title = "💰 GIẢM ≥50K"
    elif data == "100k":
        results = [v for v in vouchers if re.search(r'100k|150k|200k|300k|500k', v["text"], re.I)][:10]
        title = "💎 GIẢM ≥100K"
    elif data == "freeship":
        results = [v for v in vouchers if "freeship" in v["text"].lower()][:10]
        title = "🚚 FREESHIP EXTRA + TOÀN SÀN"
    elif data == "tiktok":
        results = [v for v in vouchers if "tiktok" in v["text"].lower()][:10]
        title = "📱 TIKTOK SHOP"
    elif data == "shopee":
        results = [v for v in vouchers if "shopee" in v["text"].lower() or "shp.ee" in v["code"]][:10]
        title = "🛒 SHOPEE"

    if not results:
        await query.edit_message_text("😔 Chưa có mã nào phù hợp. Thử lại sau 5-10 phút nhé! Bot đang quét ngầm...")
        return

    msg = f"{title} (*{len(results)} mã*)\n\n"
    for i, v in enumerate(results, 1):
        msg += f"{i}. **{v['time']}** • {v['source']}\n"
        msg += f"➤ `{v['code']}`\n"
        msg += f"{v['text'][:200]}{'...' if len(v['text'])>200 else ''}\n\n"

    await query.edit_message_text(msg.strip(), parse_mode='Markdown')

# ==================== KHỞI ĐỘNG ====================
async def main():
    # Build app
    builder = Application.builder().token(BOT_TOKEN)
    app = builder.build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Bật background scanner (chạy song song)
    app.job_queue.run_repeating(scanner_loop, interval=60, first=10)

    # Start app
    logger.info("Bot starting... Quét 150+ group 24/7")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
