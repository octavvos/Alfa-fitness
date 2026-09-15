# 🏋️ Fitness klub abonementi

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.15-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1?logo=postgresql&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.4-37814A?logo=celery&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3-26A5E4?logo=telegram&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

Fitness klub uchun abonement sotish, QR kod bilan kirish nazorati va muzlatish tizimi.
Backend — Django REST Framework + PostgreSQL, mijozlar bilan muloqot — aiogram 3 asosidagi Telegram bot.

## Mundarija

- [Xususiyatlar](#xususiyatlar)
- [Texnologiyalar](#texnologiyalar)
- [Loyiha tuzilishi](#loyiha-tuzilishi)
- [O'rnatish (lokal, Docker'siz)](#ornatish-lokal-dockersiz)
- [Docker bilan ishga tushirish](#docker-bilan-ishga-tushirish)
- [Autentifikatsiya](#autentifikatsiya)
- [API — endpointlar](#api--endpointlar)
- [Telegram bot buyruqlari va oqimlari](#telegram-bot-buyruqlari-va-oqimlari)
- [Kunlik vazifalar (Celery beat)](#kunlik-vazifalar-celery-beat)
- [Testlar](#testlar)
- [Ma'lumotlar bazasi tuzilishi haqida qisqacha](#malumotlar-bazasi-tuzilishi-haqida-qisqacha)
- [Muhim texnik eslatmalar](#muhim-texnik-eslatmalar)

## Xususiyatlar

- 📇 Mijozlar va abonement tariflarini boshqarish (admin panel API orqali)
- 📱 QR kod orqali zalga kirish nazorati — kunlik va umumiy limitlar bilan
- ❄️ Abonementni muzlatish — mijoz botdan so'raydi, admin tasdiqlaydi/rad etadi
- 🤖 Telegram bot (aiogram 3) — mijoz va admin uchun alohida oqimlar, faqat REST API orqali ishlaydi
- ⏰ Celery beat — muddati tugaganlarni avtomatik yopish, muzlatishdan chiqarish, eslatmalar yuborish
- 📊 Kunlik/hafta bo'yicha bandlik va sotuv hisobotlari
- 🐳 Docker Compose bilan bir buyruqda ishga tushirish

## Texnologiyalar

- Python 3.11+, Django 5, Django REST Framework
- PostgreSQL
- SimpleJWT (JWT autentifikatsiya)
- django-filter (filtrlash), standart PageNumberPagination (sahifalash)
- Celery + Redis — kunlik vazifalar (muddati tugaganlarni yopish, muzlatishdan chiqarish, eslatmalar)
- aiogram 3 — Telegram bot (FSM), bot faqat REST API orqali ishlaydi

## Loyiha tuzilishi

```
config/          Django sozlamalari, celery.py, urls.py
accounts/        User modeli (rol, telefon, telegram_id)
memberships/     MembershipPlan, Client, Membership, Freeze, Visit, AccessLog
api/             serializers, views, permissions, filters, celery tasks, testlar
bot/             aiogram 3 bot (admin va mijoz oqimlari)
```

## O'rnatish (lokal, Docker'siz)

> **Talab:** Python 3.11 yoki 3.12 tavsiya etiladi. Juda yangi versiyalarda (masalan 3.14) ba'zi
> kutubxonalar (`psycopg2-binary`, `Pillow`, `pydantic-core`) uchun tayyor wheel fayllar hali chiqmagan
> bo'lishi mumkin va manbadan qurish xatolik beradi. Muammo bo'lsa, [uv](https://docs.astral.sh/uv/)
> orqali kerakli versiyani osongina o'rnatish mumkin: `uv python install 3.12 && uv venv --python 3.12 .venv`.

1. Virtual muhit va kutubxonalar:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   # yoki tezroq: uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt
   ```
   QR kod skanerlash (`pyzbar`) ishlashi uchun tizimda `libzbar` kutubxonasi o'rnatilgan bo'lishi kerak:
   ```bash
   sudo apt install libzbar0        # Ubuntu 22.04 va eski versiyalar
   sudo apt install libzbar0t64     # Ubuntu 24.04+ (64-bit time_t nomlanishi)
   ```
2. `.env` faylini yarating:
   ```bash
   cp .env.example .env
   # SECRET_KEY, POSTGRES_*, BOT_TOKEN, ADMIN_CONTACT_PHONE qiymatlarini to'ldiring
   ```
3. PostgreSQL'da bazani yarating:
   ```sql
   CREATE ROLE fitness LOGIN PASSWORD 'fitness';
   CREATE DATABASE fitness OWNER fitness;
   ```
4. Migratsiya va demo ma'lumotlar:
   ```bash
   python manage.py migrate
   python manage.py seed_demo   # admin/admin12345 va 3 ta demo tarif yaratadi
   python manage.py createsuperuser  # ixtiyoriy, qo'shimcha admin uchun
   ```
5. Serverni ishga tushirish:
   ```bash
   python manage.py runserver
   ```
6. Celery worker va beat (alohida terminallarda, Redis ishlab turgan bo'lishi kerak):
   ```bash
   celery -A config worker --loglevel=info
   celery -A config beat --loglevel=info
   ```
7. Telegram bot:
   ```bash
   python -m bot.main
   ```

## Docker bilan ishga tushirish

```bash
cp .env.example .env   # BOT_TOKEN va SECRET_KEY'ni to'ldiring
docker compose up --build
```
`web`, `celery_worker`, `celery_beat`, `bot`, `db` (Postgres) va `redis` konteynerlari ishga tushadi;
`web` konteyneri migratsiya, `seed_demo` va statik fayllarni avtomatik bajaradi.

## Autentifikatsiya

- `POST /api/auth/login/` — admin uchun standart JWT login (`username`, `password`).
- `POST /api/auth/telegram-bind/` — bot ishlatadigan endpoint: `{"phone", "telegram_id"}` orqali
  foydalanuvchini (admin yoki mijoz) telefon raqami bilan topadi, `telegram_id`ni saqlaydi va
  o'sha foydalanuvchining shaxsiy JWT tokenini qaytaradi. Shu tufayli `/my/` endpointlar har doim
  `request.user` bo'yicha to'g'ri filtrlanadi — bot hech qachon boshqa birovning tokeni bilan ishlamaydi.

## API — endpointlar

| Metod | Yo'l | Kim uchun | Izoh |
|---|---|---|---|
| POST | `/api/auth/login/` | Hammasi | JWT olish (admin) |
| POST | `/api/auth/telegram-bind/` | Hammasi | Botda telefon orqali JWT olish |
| GET | `/api/plans/` | Hammasi | Abonement turlari, `?is_active=true` |
| POST/PATCH | `/api/plans/` `/api/plans/{id}/` | Admin | Tarif yaratish/tahrirlash |
| GET/POST | `/api/clients/` | Admin | Mijozlar, qidiruv: `?search=` (F.I.SH/telefon/karta) |
| GET/POST | `/api/memberships/` | Admin | Abonementlar, filter: `status`, `plan`, `end_date_from`, `end_date_to` |
| GET | `/api/memberships/my/` | Mijoz | O'z faol abonementi |
| POST | `/api/memberships/{id}/freeze/` | Admin | Muzlatish (`start_date`, `days`, `reason`) |
| POST | `/api/memberships/{id}/cancel/` | Admin | Bekor qilish |
| POST | `/api/access/check/` | Admin | QR token tekshiruvi (`qr_token`) |
| GET | `/api/visits/` | Admin | Tashriflar, filter: `date_from`, `date_to`, `client` |
| GET | `/api/visits/my/` | Mijoz | O'z tashriflari |
| GET | `/api/access-logs/` | Admin | Kirish urinishlari, filter: `result` |
| GET | `/api/reports/expiring/?days=7` | Admin | Muddati tugayotgan abonementlar |
| GET | `/api/reports/daily/?date=YYYY-MM-DD` | Admin | Kunlik tashriflar va sotuv summasi |
| GET | `/api/reports/attendance/` | Admin | So'nggi 7 kun bo'yicha soat/hafta kunlariga ko'ra bandlik |

`/api/access/check/` javobi: `{"allowed": bool, "reason": "...", "client": {...}|null, "left_days": int|null}`.
`reason` qiymatlari: `ruxsat`, `topilmadi`, `muddati_tugagan`, `muzlatilgan`, `kunlik_limit_tugagan`, `umumiy_limit_tugagan`.

## Telegram bot buyruqlari va oqimlari

- `/start` — telefon raqamni so'raydi (`request_contact`), `telegram-bind` orqali akkauntga ulanadi.
- **Mijoz menyusi:** «Mening abonementim», «QR kod» (rasm sifatida, token matn ko'rinishida yuborilmaydi),
  «Tashriflarim», «Muzlatish so'rash» (FSM: sana → kunlar → sabab → adminga tasdiqlash uchun yuboriladi).
- **Admin menyusi:** «Skanerlash» — QR rasmini (agar `pyzbar`/`libzbar0` o'rnatilgan bo'lsa avtomatik o'qiydi)
  yoki tokenni matn sifatida qabul qiladi, `POST /api/access/check/` chaqiradi va natijani yashil/qizil
  xabar bilan ko'rsatadi. Muzlatish so'rovlariga «✅ Tasdiqlash / ❌ Rad etish» inline tugmalari orqali javob beradi.

## Kunlik vazifalar (Celery beat)

- `00:05` — `expire_memberships`: muddati tugagan faol abonementlarni `tugagan` statusiga o'tkazadi.
- `00:10` — `unfreeze_memberships`: muzlatish davri tugagan abonementlarni `faol` statusiga qaytaradi.
- `10:00` — `send_expiry_reminders`: 3 kundan kam qolganlarga eslatma, bugun tugaganlarga yangilash taklifi
  yuboradi; `Membership.reminder_sent_at` orqali bir kunda ikki marta yubormaydi.

## Testlar

Loyihaning qiyin qismi — QR kod orqali kirish nazorati (`AccessCheckView`) — uchun `api/tests.py`
ichida to'rtala asosiy holat (muddati tugagan, muzlatilgan, kunlik limit, yaroqsiz token) va qo'shimcha
holatlar (ruxsat, umumiy limit, ikki marta skanerlash) test qilingan:

```bash
python manage.py test
```

## Ma'lumotlar bazasi tuzilishi haqida qisqacha

- `User` — `AbstractUser`dan meros, `role`/`phone`/`telegram_id` bilan; `phone` mijozni telefon orqali
  topish uchun unique kalit, `telegram_id` bot bog'langanda to'ladi.
- `Client` — `User` bilan `OneToOne` (har bir mijoz — bitta akkaunt), zalga oid ma'lumotlar (F.I.SH, karta) shu yerda.
- `Membership` — `Client` va `MembershipPlan`ga `PROTECT` bilan bog'langan (tarif yoki mijoz o'chirilsa,
  tarix yo'qolmasin). `price_paid` tarif narxining nusxasi — keyinchalik narx o'zgarsa, eski
  abonementlarning to'lov tarixi buzilmaydi. `UniqueConstraint(client, condition=status='faol')` — bir
  mijozda bitta faol abonement qoidasini DB darajasida ta'minlaydi.
- `Freeze` — `Membership`ga `CASCADE` (abonement o'chsa, uning muzlatish tarixi ham keraksiz), muzlatish
  kunlari yig'indisi va davrlar kesishmasligi serializer darajasida tekshiriladi.
- `Visit` — `Membership`ga `PROTECT` (tashrif tarixi hech qachon yo'qolmasin), `(membership, checked_in_at)`
  indeksi kunlik limitni tez hisoblash uchun.
- `AccessLog` — `Membership`ga `SET_NULL` (topilmagan yoki noto'g'ri tokenlar ham yozilishi kerak, shuning
  uchun FK ixtiyoriy) — nizolarda dalil sifatida barcha urinishlar saqlanadi.

## Muhim texnik eslatmalar

- QR kodda faqat `qr_token` (tasodifiy UUID) bo'ladi — mijozning telefon raqami yoki ID'si emas.
- `/api/access/check/` butun tekshiruvi `transaction.atomic()` + `select_for_update()` ichida bajariladi,
  shu sababli bitta QR kodni bir vaqtda ikki marta skanerlash ikkita tashrif yozib qo'ymaydi.
- Har bir tekshiruv natijasi (ruxsat berilgan yoki berilmagan) `AccessLog`ga yoziladi.
- Bot backenddagi ma'lumotlar bazasiga to'g'ridan-to'g'ri ulanmaydi — faqat REST API orqali ishlaydi.
