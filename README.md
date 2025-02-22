# 🎵 Spotify Telegram Bot

Bot Telegram tích hợp với Spotify, cho phép người dùng quản lý và xem thông tin về hoạt động nghe nhạc của họ trên Spotify.

## ✨ Tính năng

- 🎵 Xem thông tin bài hát đang phát
- 🏆 Xem top bài hát yêu thích
- 📋 Quản lý và xem playlist
- ❤️ Xem danh sách bài hát đã lưu
- 📊 Xem thống kê tài khoản
- 🔄 Xem lịch sử nghe nhạc
- ⚙️ Tùy chỉnh số lượng hiển thị

## 🚀 Cài đặt

### Yêu cầu

- Python 3.9 trở lên
- Tài khoản Telegram
- Tài khoản Spotify `Premium`

### Các bước cài đặt

1. Clone repository:
```bash
git clone https://github.com/tanbaycu/spotifybot.git
cd spotifybot
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Tạo file .env và thêm các biến môi trường:
```bash
TELEGRAM_TOKEN=your_telegram_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
```

4. Chạy bot:
```python
python bot.py
```

## 📝 Cấu hình

### Telegram Bot Token

1. Truy cập @BotFather trên Telegram
2. Tạo bot mới với lệnh /newbot
3. Lưu token được cấp

### Spotify API Credentials

1. Truy cập Spotify Developer Dashboard
2. Tạo ứng dụng mới
3. Lưu Client ID và Client Secret
4. Thêm Redirect URI trong cài đặt ứng dụng

## 💡 Sử dụng

### Các lệnh cơ bản

- /start - Bắt đầu bot và xác thực với Spotify
- /menu - Hiển thị menu chính
- /set_token - Nhập token sau khi xác thực Spotify
- /logout - Đăng xuất khỏi tài khoản Spotify

### Cài đặt tùy chỉnh

- /set_amount <số> - Điều chỉnh số lượng hiển thị (1-50)
- /settings - Xem cài đặt hiện tại
- /contact - Xem thông tin về bot và nhà phát triển

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Hãy:

1. Fork dự án
2. Tạo branch mới (git checkout -b feature/AmazingFeature)
3. Commit thay đổi (git commit -m 'Add some AmazingFeature')
4. Push lên branch (git push origin feature/AmazingFeature)
5. Tạo Pull Request


## 📞 Liên hệ

- Telegram: @tanbaycu
- Email: tanbaycu@gmail.com
- Website: https://tanbaycu.vercel.app

## 🙏 Cảm ơn

- python-telegram-bot: https://github.com/python-telegram-bot/python-telegram-bot
- spotipy: https://github.com/plamere/spotipy
- Spotify Web API: https://developer.spotify.com/documentation/web-api

## 📝 Changelog

### [1.0.0] - 2024-02-22
- Phát hành phiên bản đầu tiên
- Thêm các tính năng cơ bản
- Tích hợp với Spotify API
- Thêm tính năng tùy chỉnh số lượng hiển thị