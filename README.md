# HR Filtrlash Boti

Telegram orqali nomzodlarni ketma-ket savollar bilan filtrlaydigan, mos kelganlaridan CV
so'raydigan va adminlarga (Telegram + email) bildirishnoma yuboradigan bot.

## 1. Talablar

- Python 3.11+
- Telegram bot tokeni ([@BotFather](https://t.me/BotFather))
- Google Cloud loyihasi (Service Account, Sheets API, Drive API)
- SMTP hisobi (email bildirishnoma uchun, ixtiyoriy)
- Docker + Docker Compose (production uchun tavsiya etiladi)

## 2. Telegram bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) bilan suhbat oching.
2. `/newbot` buyrug'ini yuboring, botga nom va username bering (masalan `HRMillinaBot`).
3. BotFather bergan tokenni `.env` faylidagi `BOT_TOKEN` ga qo'ying.
4. O'zingizning Telegram ID'ingizni bilish uchun [@userinfobot](https://t.me/userinfobot) ga
   yozing va olingan raqamni `ADMIN_CHAT_IDS` ga qo'ying (bir nechta admin bo'lsa, vergul bilan
   ajrating).

## 3. Google Cloud Service Account yaratish

1. [Google Cloud Console](https://console.cloud.google.com/) da yangi loyiha yarating (yoki
   mavjudini tanlang).
2. **APIs & Services → Library** bo'limidan quyidagilarni yoqing:
   - Google Sheets API
   - Google Drive API
3. **APIs & Services → Credentials → Create Credentials → Service Account** orqali yangi
   service account yarating.
4. Yaratilgan service account ichida **Keys → Add Key → Create new key → JSON** tanlang — fayl
   yuklab olinadi. Uni loyiha papkasiga `credentials.json` nomi bilan saqlang (bu fayl hech
   qachon Git'ga qo'shilmasin — `.gitignore`'da allaqachon istisno qilingan).
5. Service account emailini (masalan `hr-bot@loyiha.iam.gserviceaccount.com`) nusxalab oling.

### Google Sheets ulash

1. Yangi Google Sheets jadval yarating.
2. Jadvalni yuqoridagi service account emailiga **Editor** huquqi bilan ulashing (Share tugmasi).
3. Jadval URL'idagi ID qismini (`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`)
   `.env` faylidagi `GOOGLE_SHEET_ID` ga qo'ying.
4. Bot birinchi marta yozganda sarlavha qatorini avtomatik yaratadi.

### Google Drive papkasi

1. Google Drive'da CV fayllar uchun papka yarating (masalan `HR_Bot_CVlar`).
2. Papkani ham service account emailiga **Editor** huquqi bilan ulashing.
3. Papka ID'sini (papka URL'idagi oxirgi qism) `.env` faylidagi `GOOGLE_DRIVE_FOLDER_ID` ga
   qo'ying.

> **Muhim eslatma**: 2021-yildan buyon oddiy service account'lar shaxsiy Google Drive kvotasiga
> ega emas. Agar fayl yuklashda kvota xatoligi chiqsa, ikkita yechim bor:
> 1. Papkani **Shared Drive** (Google Workspace) ichida yarating — service account shu Shared
>    Drive'ga a'zo qilinsa, fayllar muammosiz yuklanadi.
> 2. Yoki Google Workspace domenida **domain-wide delegation** yoqib, `.env` faylidagi
>    `GOOGLE_IMPERSONATE_EMAIL` ga haqiqiy foydalanuvchi emailini yozing — bot shu foydalanuvchi
>    nomidan fayl yuklaydi.

## 4. Email (SMTP) sozlash

`.env` faylida quyidagilarni to'ldiring:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=sizning-emailingiz@gmail.com
SMTP_PASSWORD=<App Password>
SMTP_FROM=sizning-emailingiz@gmail.com
NOTIFY_EMAIL_TO=OAbdujalilov@nbu.uz
```

Agar Gmail ishlatilsa: oddiy parol ishlamaydi, **App Password** kerak bo'ladi:
1. Google hisobingizda 2-bosqichli tasdiqlashni (2FA) yoqing.
2. [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) sahifasiga
   kiring, yangi App Password yarating va uni `SMTP_PASSWORD` ga qo'ying.

Agar `SMTP_HOST` bo'sh qoldirilsa, bot email yubormaydi, lekin Telegram bildirishnomasi va
Google Sheets yozuvi baribir ishlaydi (email — qo'shimcha, ixtiyoriy kanal).

## 5. Mahalliy ishga tushirish (development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env faylini to'ldiring, credentials.json faylini loyiha papkasiga joylashtiring

python bot.py
```

## 6. Docker orqali serverda ishga tushirish (production)

```bash
cp .env.example .env
# .env faylini to'ldiring
# credentials.json faylini loyiha papkasiga qo'ying

touch fallback_log.jsonl   # bind mount uchun fayl oldindan mavjud bo'lishi kerak

docker compose up -d --build
```

Foydali buyruqlar:

```bash
docker compose logs -f        # loglarni kuzatish
docker compose restart        # botni qayta ishga tushirish
docker compose down           # to'xtatish
```

`docker-compose.yml`da `restart: always` o'rnatilgan — server qayta yuklansa ham bot avtomatik
ishga tushadi.

## 7. Loyiha tuzilmasi

```
BotJavohir/
├── bot.py                # kirish nuqtasi (polling, router ro'yxati, logging)
├── config.py              # .env'ni o'qish/tekshirish
├── states.py               # FSM holatlari
├── criteria.py              # 5 ta savol va mos javoblar - yagona konfiguratsiya manbai
├── texts/
│   └── texts.py             # uz/ru barcha interfeys matnlari
├── keyboards/
│   └── inline.py             # inline tugmalar
├── services/
│   ├── sheets.py              # Google Sheets bilan ishlash
│   ├── drive.py                # Google Drive'ga CV yuklash
│   ├── email_service.py         # SMTP orqali bildirishnoma
│   └── fallback.py               # Sheets ishlamasa - fallback_log.jsonl
└── handlers/
    ├── start.py                  # /start, til tanlash
    ├── questions.py               # 5 ta filtr savoli
    ├── cv.py                       # CV qabul qilish, admin/email bildirishnoma
    ├── admin.py                     # /stats, /export
    └── common.py                     # umumiy yordamchi funksiyalar
```

## 8. Mezonlarni o'zgartirish

Savollar matni, variantlar va qaysi javob "mos" hisoblanishi butunlay `criteria.py` faylida
saqlanadi. Yangi savol qo'shish, variant o'zgartirish yoki mos javoblar ro'yxatini yangilash
uchun faqat shu faylni tahrirlash kifoya — handlerlar kodiga tegish shart emas.

## 9. Admin paneli

`.env`dagi `ADMIN_CHAT_IDS` ro'yxatidagi foydalanuvchi botga `/start` yuborsa, oddiy til
tanlash o'rniga tugmali admin menyusi chiqadi:

- **📊 Statistika** — jami arizalar, mos/mos emas soni, rad etilgan bosqichlar bo'yicha taqsimot
- **📁 So'nggi CV'lar** — oxirgi mos nomzodlar ro'yxati (tugma sifatida); har birini bosganda
  to'liq ma'lumot va Google Drive havolasi ko'rsatiladi
- **📤 Excel eksport** — Google Sheets'dagi barcha ma'lumotni `.xlsx` fayl qilib yuboradi

Xuddi shu amallar matnli buyruqlar sifatida ham ishlaydi: `/stats`, `/export`.

Eslatma: har bir mos nomzodning CV fayli ariza kelgan zahoti adminlarga to'g'ridan-to'g'ri
forward qilinadi (5.1-bo'lim) — "📁 So'nggi CV'lar" tugmasi esa arxivni keyinroq qayta ko'rish
uchun.

Bu buyruq va menyular faqat `ADMIN_CHAT_IDS` ro'yxatidagilar uchun ishlaydi; oddiy nomzodlar
uchun `/start` har doim odatdagidek til tanlashdan boshlanadi.

## 10. Loglar va fallback

- Barcha xatoliklar va muhim hodisalar `logs/bot.log` fayliga yoziladi (rotatsiya bilan, 5MB x 5
  nusxa).
- Agar Google Sheets vaqtincha ishlamay qolsa, nomzod ma'lumoti `fallback_log.jsonl` fayliga
  JSON qator sifatida yoziladi — keyinchalik qo'lda Sheets'ga kiritish uchun.
