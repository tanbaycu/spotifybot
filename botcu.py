import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
import json
from datetime import datetime

# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "https://tanbaycu.vercel.app/spotify_auth"

SPOTIFY_SCOPE = "user-read-currently-playing user-top-read user-read-recently-played playlist-read-private user-library-read user-read-email user-read-private user-follow-read"

# Lưu trữ token và cài đặt người dùng
user_data = {}
DEFAULT_AMOUNT = 5
MAX_AMOUNT = 50  # Giới hạn tối đa để tránh spam và lỗi API

sp_oauth = SpotifyOAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, scope=SPOTIFY_SCOPE)

# Định nghĩa các lệnh và nút tương ứng
COMMANDS = {
    "current": "🎵 Bài hát đang nghe",
    "top": "🏆 Top bài hát",
    "playlists": "📋 Playlist",
    "liked": "❤️ Bài hát yêu thích",
    "stats": "📊 Thống kê",
    "recent": "🔄 Cập nhật gần đây",
    "help": "ℹ️ Trợ giúp",
    "settings": "⚙️ Cài đặt"
}

def get_main_keyboard():
    keyboard = [[KeyboardButton(text)] for text in COMMANDS.values()]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def init_user_data(user_id: str) -> None:
    """Khởi tạo dữ liệu người dùng nếu chưa tồn tại"""
    if user_id not in user_data:
        user_data[user_id] = {
            'token': None,
            'amount': DEFAULT_AMOUNT,
            'last_command': None
        }

def get_user_amount(user_id: str) -> int:
    """Lấy số lượng kết quả đã cài đặt của người dùng"""
    init_user_data(user_id)
    return user_data[user_id].get('amount', DEFAULT_AMOUNT)

def escape_markdown(text: str) -> str:
    """Escape các ký tự đặc biệt trong Markdown."""
    if not text:
        return ""
    # Đối với Markdown thông thường, chỉ cần escape một số ký tự
    special_chars = ['[', ']', '(', ')', '_', '*', '`']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def get_current_track(update: Update, sp: spotipy.Spotify) -> None:
    """Lấy thông tin bài hát đang phát."""
    try:
        current_track = sp.current_user_playing_track()
        if current_track is not None and current_track['is_playing']:
            track = current_track['item']
            artist = escape_markdown(track['artists'][0]['name'])
            track_name = escape_markdown(track['name'])
            album = escape_markdown(track['album']['name'])
            duration = track['duration_ms'] // 1000
            progress = current_track['progress_ms'] // 1000
            
            # Thêm thông tin chi tiết
            album_type = track['album']['album_type'].capitalize()
            release_date = track['album']['release_date']
            track_number = track['track_number']
            total_tracks = track['album']['total_tracks']
            popularity = track['popularity']
            
            # Tạo thanh tiến trình
            progress_bar_length = 20
            progress_ratio = progress / duration
            filled = int(progress_bar_length * progress_ratio)
            progress_bar = '▓' * filled + '░' * (progress_bar_length - filled)
            
            response = (
                f"🎵 *Đang phát:* {track_name}\n"
                f"👤 *Nghệ sĩ:* {artist}\n"
                f"💿 *Album:* {album}\n"
                f"📀 *Loại album:* {album_type}\n"
                f"📅 *Ngày phát hành:* {release_date}\n"
                f"🔢 *Track:* {track_number}/{total_tracks}\n"
                f"🌟 *Độ phổ biến:* {popularity}/100\n\n"
                f"⏳ *Thời gian:* {progress//60}:{progress%60:02d}/{duration//60}:{duration%60:02d}\n"
                f"`{progress_bar}` {int(progress_ratio * 100)}%"
            )
            
            # Thêm preview URL nếu có
            if track.get('preview_url'):
                response += f"\n\n🎧 [Nghe thử 30s]({track['preview_url']})"
            
            # Thêm link Spotify
            response += f"\n🔗 [Mở trên Spotify]({track['external_urls']['spotify']})"
            
        else:
            response = "🔇 *Không có bài hát nào đang phát*"
        
        await update.message.reply_text(response, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in get_current_track: {e}")
        await update.message.reply_text(
            "❌ *Có lỗi xảy ra khi lấy thông tin bài hát.*",
            parse_mode='Markdown'
        )

async def get_stats(update: Update, sp: spotipy.Spotify) -> None:
    """Lấy thống kê chi tiết về tài khoản Spotify."""
    try:
        # Lấy thông tin người dùng
        user_info = sp.current_user()
        followed_artists = sp.current_user_followed_artists()
        playlists = sp.current_user_playlists()
        saved_tracks = sp.current_user_saved_tracks()
        top_artists = sp.current_user_top_artists(limit=3, time_range='short_term')
        recently_played = sp.current_user_recently_played(limit=1)
        
        # Tính toán thống kê
        total_playlists = playlists['total']
        total_saved = saved_tracks['total']
        total_following = followed_artists['artists']['total']
        
        # Tạo phản hồi
        response = [
            "📊 *Thống kê tài khoản Spotify của bạn:*\n",
            f"👤 *Tên người dùng:* {escape_markdown(user_info['display_name'])}",
            f"🌍 *Quốc gia:* {user_info.get('country', 'N/A')}",
            f"📧 *Email:* {user_info.get('email', 'N/A')}",
            f"🎵 *Gói dịch vụ:* {user_info['product'].capitalize()}",
            f"👥 *Đang theo dõi:* {total_following} nghệ sĩ",
            f"📋 *Playlist:* {total_playlists}",
            f"❤️ *Bài hát đã lưu:* {total_saved}"
        ]

        # Thêm nghệ sĩ yêu thích
        if top_artists['items']:
            response.append("\n🌟 *Top nghệ sĩ gần đây:*")
            for i, artist in enumerate(top_artists['items'], 1):
                response.append(f"{i}. {escape_markdown(artist['name'])}")

        # Thêm bài hát gần đây nhất
        if recently_played['items']:
            last_played = recently_played['items'][0]['track']
            response.append(
                f"\n🎵 *Bài hát nghe gần đây nhất:*\n"
                f"{escape_markdown(last_played['name'])} - {escape_markdown(last_played['artists'][0]['name'])}"
            )

        # Thêm liên kết hồ sơ
        if user_info.get('external_urls', {}).get('spotify'):
            response.append(f"\n🔗 [Xem hồ sơ trên Spotify]({user_info['external_urls']['spotify']})")

        await update.message.reply_text(
            '\n'.join(response),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        await update.message.reply_text(
            "❌ *Có lỗi xảy ra khi lấy thống kê.*",
            parse_mode='Markdown'
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    init_user_data(user_id)
    
    if user_data[user_id].get('token'):
        await show_main_menu(update, context)
    else:
        auth_url = sp_oauth.get_authorize_url(state=user_id)
        keyboard = [[InlineKeyboardButton("🔑 Xác thực Spotify", url=auth_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "*Chào mừng bạn đến với Spotify Bot!*\n\n"
            "Để bắt đầu, hãy làm theo các bước sau:\n"
            "1. Nhấn nút bên dưới để xác thực với Spotify\n"
            "2. Sau khi xác thực thành công, copy token nhận được\n"
            "3. Quay lại đây và sử dụng lệnh /set\\_token để nhập token"
        )
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    init_user_data(user_id)
    
    current_amount = get_user_amount(user_id)
    settings_text = (
        "*⚙️ Cài đặt hiện tại:*\n\n"
        f"📊 *Số lượng hiển thị:* {current_amount}\n"
        f"🔒 *Trạng thái:* {'*Đã đăng nhập*' if user_data[user_id].get('token') else '*Chưa đăng nhập*'}\n\n"
        "*Các lệnh cài đặt:*\n"
        "• `/set_amount <số>` - Điều chỉnh số lượng hiển thị\n"
        "• `/logout` - Đăng xuất\n"
        "• `/start` - Đăng nhập lại"
    )
    
    await update.message.reply_text(
        settings_text,
        parse_mode='Markdown'
    )

async def show_help(update: Update) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    help_text = f"""
*🤖 Hướng dẫn sử dụng Spotify Bot:*

• Sử dụng các nút trên bàn phím tùy chỉnh để chọn chức năng
• Số lượng hiển thị hiện tại: *{amount}* mục

*Các lệnh cơ bản:*
• `/start` - Bắt đầu bot và xác thực với Spotify
• `/menu` - Hiển thị menu chính
• `/set_token` - Nhập token sau khi xác thực Spotify
• `/logout` - Đăng xuất khỏi tài khoản Spotify

*Cài đặt tùy chỉnh:*
• `/set_amount <số>` - Điều chỉnh số lượng hiển thị (1-{MAX_AMOUNT})
• `/settings` - Xem cài đặt hiện tại

*Lưu ý:*
• Số lượng tối đa có thể hiển thị là {MAX_AMOUNT} mục
• Nếu gặp lỗi, hãy thử đăng xuất và đăng nhập lại
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def get_top_tracks(update: Update, sp: spotipy.Spotify) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    try:
        top_tracks = sp.current_user_top_tracks(limit=amount, time_range='short_term')
        response = [f"*🏆 Top {amount} bài hát của bạn trong thời gian gần đây:*\n"]
        
        if not top_tracks['items']:
            response = ["*❗ Không có dữ liệu về top bài hát.*"]
        else:
            for i, track in enumerate(top_tracks['items'], 1):
                track_name = escape_markdown(track['name'])
                artist_name = escape_markdown(track['artists'][0]['name'])
                popularity = track['popularity']
                stars = '⭐' * ((popularity + 19) // 20)  # Convert popularity to 1-5 stars
                response.append(f"{i}. *{track_name}* - {artist_name} {stars}")
        
        await update.message.reply_text('\n'.join(response), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in get_top_tracks: {e}")
        await update.message.reply_text(
            "*❌ Có lỗi xảy ra khi lấy danh sách top bài hát.*",
            parse_mode='Markdown'
        )

async def get_playlists(update: Update, sp: spotipy.Spotify) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    try:
        playlists = sp.current_user_playlists(limit=amount)
        response = [f"*📋 {amount} playlist gần đây của bạn:*\n"]
        
        if not playlists['items']:
            response = ["*❗ Bạn chưa có playlist nào.*"]
        else:
            for i, playlist in enumerate(playlists['items'], 1):
                playlist_name = escape_markdown(playlist['name'])
                tracks_count = playlist['tracks']['total']
                response.append(f"{i}. *{playlist_name}* ({tracks_count} bài hát)")
        
        await update.message.reply_text('\n'.join(response), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in get_playlists: {e}")
        await update.message.reply_text(
            "*❌ Có lỗi xảy ra khi lấy danh sách playlist.*",
            parse_mode='Markdown'
        )

async def get_liked_songs(update: Update, sp: spotipy.Spotify) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    try:
        liked_songs = sp.current_user_saved_tracks(limit=amount)
        response = [f"*❤️ {amount} bài hát yêu thích gần đây của bạn:*\n"]
        
        if not liked_songs['items']:
            response = ["*❗ Bạn chưa có bài hát yêu thích nào.*"]
        else:
            for i, item in enumerate(liked_songs['items'], 1):
                track = item['track']
                track_name = escape_markdown(track['name'])
                artist_name = escape_markdown(track['artists'][0]['name'])
                # Thêm thông tin thêm như độ phổ biến
                popularity = track['popularity']
                stars = '⭐' * ((popularity + 19) // 20)  # Convert popularity to 1-5 stars
                response.append(f"{i}. *{track_name}* - {artist_name} {stars}")
        
        await update.message.reply_text('\n'.join(response), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in get_liked_songs: {e}")
        await update.message.reply_text(
            "*❌ Có lỗi xảy ra khi lấy danh sách bài hát yêu thích.*",
            parse_mode='Markdown'
        )

async def get_recent_activity(update: Update, sp: spotipy.Spotify) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    try:
        recently_played = sp.current_user_recently_played(limit=amount)
        response = [f"*🔄 {amount} hoạt động gần đây:*\n"]
        
        if not recently_played['items']:
            response = ["*❗ Không có hoạt động nghe nhạc gần đây.*"]
        else:
            for i, item in enumerate(recently_played['items'], 1):
                track = item['track']
                track_name = escape_markdown(track['name'])
                artist_name = escape_markdown(track['artists'][0]['name'])
                
                # Tính thời gian
                played_at = datetime.strptime(item['played_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
                time_diff = datetime.utcnow() - played_at
                
                if time_diff.days > 0:
                    time_str = f"{time_diff.days} ngày trước"
                elif time_diff.seconds // 3600 > 0:
                    time_str = f"{time_diff.seconds // 3600} giờ trước"
                else:
                    time_str = f"{time_diff.seconds // 60} phút trước"
                
                response.append(f"{i}. *{track_name}* - {artist_name} ({time_str})")
        
        await update.message.reply_text('\n'.join(response), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in get_recent_activity: {e}")
        await update.message.reply_text(
            "*❌ Có lỗi xảy ra khi lấy lịch sử hoạt động.*",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    init_user_data(user_id)

    if not user_data[user_id].get('token'):
        await update.message.reply_text(
            "*Bạn chưa đăng nhập. Vui lòng sử dụng /start để bắt đầu quá trình xác thực.*",
            parse_mode='Markdown'
        )
        return

    sp = spotipy.Spotify(auth=user_data[user_id]['token'])

    try:
        if message_text == COMMANDS["current"]:
            await get_current_track(update, sp)
        elif message_text == COMMANDS["top"]:
            await get_top_tracks(update, sp)
        elif message_text == COMMANDS["playlists"]:
            await get_playlists(update, sp)
        elif message_text == COMMANDS["liked"]:
            await get_liked_songs(update, sp)
        elif message_text == COMMANDS["stats"]:
            await get_stats(update, sp)
        elif message_text == COMMANDS["recent"]:
            await get_recent_activity(update, sp)
        elif message_text == COMMANDS["help"]:
            await show_help(update)
        elif message_text == COMMANDS["settings"]:
            await show_settings(update, context)
        else:
            await update.message.reply_text(
                "*❌ Lệnh không hợp lệ. Vui lòng sử dụng menu hoặc /help để xem danh sách lệnh.*",
                parse_mode='Markdown'
            )

    except spotipy.SpotifyException as e:
        logger.error(f"Spotify error: {e}")
        if 'The access token expired' in str(e):
            await update.message.reply_text(
                "*⚠️ Phiên đăng nhập đã hết hạn. Vui lòng sử dụng /start để xác thực lại.*",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "*❌ Có lỗi xảy ra khi truy cập Spotify. Vui lòng thử lại sau.*",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text(
            "*❌ Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.*",
            parse_mode='Markdown'
        )

async def set_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        token_info = json.loads(update.message.text.split(' ', 1)[1])
        user_id = str(update.effective_user.id)
        init_user_data(user_id)
        user_data[user_id]['token'] = token_info['access_token']
        
        # Xóa tin nhắn chứa token để bảo mật
        await update.message.delete()
        
        await update.message.reply_text(
            "*✅ Token đã được lưu thành công. Bạn có thể sử dụng các chức năng của bot ngay bây giờ.*",
            parse_mode='Markdown'
        )
        await show_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error setting token: {e}")
        await update.message.reply_text(
            "*❌ Có lỗi xảy ra khi lưu token. Vui lòng thử lại.*",
            parse_mode='Markdown'
        )

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    init_user_data(user_id)
    
    if user_data[user_id].get('token'):
        user_data[user_id]['token'] = None
        await update.message.reply_text(
            "*🚪 Bạn đã đăng xuất thành công. Sử dụng /start để đăng nhập lại.*",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "*❗ Bạn chưa đăng nhập. Sử dụng /start để bắt đầu.*",
            parse_mode='Markdown'
        )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    await update.message.reply_text(
        f"*🎧 Menu Chính - Chọn một tùy chọn:*\n"
        f"Số lượng hiển thị hiện tại: *{amount}* mục",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    init_user_data(user_id)
    
    try:
        # Kiểm tra xem có đối số không
        if not context.args:
            current_amount = get_user_amount(user_id)
            await update.message.reply_text(
                f"*🔢 Cài đặt số lượng hiện tại:* {current_amount}\n"
                f"Để thay đổi, hãy sử dụng: `/set_amount <số lượng>` (1-{MAX_AMOUNT})",
                parse_mode='Markdown'
            )
            return

        amount = int(context.args[0])
        
        # Kiểm tra giới hạn
        if amount < 1 or amount > MAX_AMOUNT:
            await update.message.reply_text(
                f"*❌ Số lượng phải từ 1 đến {MAX_AMOUNT}.*",
                parse_mode='Markdown'
            )
            return
        
        user_data[user_id]['amount'] = amount
        await update.message.reply_text(
            f"*✅ Đã cập nhật số lượng hiển thị thành: {amount}*",
            parse_mode='Markdown'
        )
        
    except ValueError:
        await update.message.reply_text(
            "*❌ Vui lòng nhập một số hợp lệ.*",
            parse_mode='Markdown'
        )

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    init_user_data(user_id)
    
    current_amount = get_user_amount(user_id)
    settings_text = (
        "*⚙️ Cài đặt hiện tại:*\n\n"
        f"📊 *Số lượng hiển thị:* {current_amount}\n"
        f"🔒 *Trạng thái:* {'*Đã đăng nhập*' if user_data[user_id].get('token') else '*Chưa đăng nhập*'}\n\n"
        "*Các lệnh cài đặt:*\n"
        "• `/set_amount <số>` - Điều chỉnh số lượng hiển thị\n"
        "• `/logout` - Đăng xuất\n"
        "• `/start` - Đăng nhập lại"
    )
    
    await update.message.reply_text(
        settings_text,
        parse_mode='Markdown'
    )

async def show_help(update: Update) -> None:
    user_id = str(update.effective_user.id)
    amount = get_user_amount(user_id)
    
    help_text = f"""
*🤖 Hướng dẫn sử dụng Spotify Bot:*

• Sử dụng các nút trên bàn phím tùy chỉnh để chọn chức năng
• Số lượng hiển thị hiện tại: *{amount}* mục

*Các lệnh cơ bản:*
• `/start` - Bắt đầu bot và xác thực với Spotify
• `/menu` - Hiển thị menu chính
• `/set_token` - Nhập token sau khi xác thực Spotify
• `/logout` - Đăng xuất khỏi tài khoản Spotify

*Cài đặt tùy chỉnh:*
• `/set_amount <số>` - Điều chỉnh số lượng hiển thị (1-{MAX_AMOUNT})
• `/settings` - Xem cài đặt hiện tại

*Thông tin khác:*
• `/contact` - Xem thông tin về bot và nhà phát triển

*Lưu ý:*
• Số lượng tối đa có thể hiển thị là {MAX_AMOUNT} mục
• Nếu gặp lỗi, hãy thử đăng xuất và đăng nhập lại
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Thêm hàm xử lý lệnh /contact
async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị thông tin liên hệ và thông tin về bot"""
    contact_info = """
*🤖 Thông tin về Spotify Bot*

*Phiên bản:* 1.0.0
*Ngôn ngữ:* Python
*Framework:* python-telegram-bot, Spotipy
*Ngày phát hành:* 22/02/2024

*👨‍💻 Thông tin nhà phát triển*
*Tên:* tanbaycu
*Email:* tanbaycu@gmail.com
*GitHub:* [tanbaycu](https://github.com/tanbaycu)
*Facebook:* [Tran Minh Tan](https://facebook.com/tanbaycu.kaiser)

*📝 Tính năng chính*
• Xem thông tin bài hát đang phát
• Xem top bài hát yêu thích
• Quản lý playlist
• Thống kê hoạt động nghe nhạc
• Tùy chỉnh số lượng hiển thị

*🔗 Liên kết hữu ích*
• [Báo cáo lỗi](https://t.me/tanbaycu)
• [Đóng góp phát triển](https://github.com/tanbaycu/spotify-bot)

*💝 Hỗ trợ phát triển*
Nếu bạn thấy bot hữu ích, hãy:
• Chia sẻ cho bạn bè
• Star dự án trên GitHub
• Đóng góp ý kiến phát triển

*📮 Liên hệ hỗ trợ*
• Telegram: @tanbaycu
• Discord: tanbaycu
"""
    await update.message.reply_text(
        contact_info,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Thêm các handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(CommandHandler("set_token", set_token))
    application.add_handler(CommandHandler("set_amount", set_amount))
    application.add_handler(CommandHandler("settings", show_settings))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bắt đầu bot
    application.run_polling()

if __name__ == "__main__":
    main()