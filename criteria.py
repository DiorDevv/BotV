"""
Filtrlash savollari va mezonlari - yagona manba.

Har bir savolni yoki mos javoblar ro'yxatini o'zgartirish uchun faqat shu
faylni tahrirlash kifoya - handlerlar kodini o'zgartirish shart emas.

Savollar ketma-ketligi qat'iy: age -> education_direction -> degree ->
course -> education_form -> (CV so'rash).
"""
from states import Form

# Savollar ko'rsatiladigan tartib
QUESTION_ORDER = ["age", "education_direction", "degree", "course", "education_form"]

QUESTIONS = {
    "age": {
        "state": Form.age,
        "next": "education_direction",
        "sheet_column": "Yosh javobi",
        "reject_label": {"uz": "Yosh", "ru": "Возраст"},
        "question": {
            "uz": "Yoshingizni tanlang",
            "ru": "Выберите ваш возраст",
        },
        "options": [
            {"id": "18_20", "uz": "18–20 yosh", "ru": "18–20 лет"},
            {"id": "21_30", "uz": "21–30 yosh", "ru": "21–30 лет"},
            {"id": "30_plus", "uz": "30 yoshdan baland", "ru": "старше 30 лет"},
        ],
        "accepted": {"21_30"},
    },
    "education_direction": {
        "state": Form.education_direction,
        "next": "degree",
        "sheet_column": "Ta'lim yo'nalishi javobi",
        "reject_label": {"uz": "Ta'lim yo'nalishi", "ru": "Направление образования"},
        "question": {
            "uz": "Ta'lim yo'nalishingizni tanlang",
            "ru": "Выберите направление вашего образования",
        },
        "options": [
            {
                "id": "iqtisodiy",
                "uz": "Iqtisodiy toifadagi mutaxassisliklar",
                "ru": "Специальности экономического профиля",
            },
            {
                "id": "it",
                "uz": "IT toifadagi mutaxassisliklar",
                "ru": "Специальности IT-профиля",
            },
            {
                "id": "biznes",
                "uz": "Biznes boshqaruvi toifadagi mutaxassisliklar",
                "ru": "Специальности по направлению «Управление бизнесом»",
            },
            {"id": "boshqa", "uz": "Boshqa", "ru": "Другое"},
        ],
        "accepted": {"iqtisodiy"},
    },
    "degree": {
        "state": Form.degree,
        "next": "course",
        "sheet_column": "Ilmiy daraja javobi",
        "reject_label": {"uz": "Ilmiy daraja", "ru": "Учёная степень"},
        "question": {
            "uz": "Ilmiy darajangizni tanlang",
            "ru": "Выберите вашу учёную степень",
        },
        "options": [
            {"id": "orta_maxsus", "uz": "O'rta maxsus", "ru": "Среднее специальное"},
            {"id": "bakalavr", "uz": "Bakalavr", "ru": "Бакалавр"},
            {"id": "magistr", "uz": "Magistr", "ru": "Магистр"},
            {"id": "phd", "uz": "PhD (Fan doktori)", "ru": "PhD (доктор философии)"},
            {"id": "dsc", "uz": "DSc (Fan doktori)", "ru": "DSc (доктор наук)"},
            {"id": "boshqa", "uz": "Boshqa", "ru": "Другое"},
        ],
        "accepted": {"bakalavr", "magistr", "phd", "dsc"},
    },
    "course": {
        "state": Form.course,
        "next": "education_form",
        "sheet_column": "Kurs javobi",
        "reject_label": {"uz": "Kurs", "ru": "Курс"},
        "question": {
            "uz": "Kursingizni tanlang",
            "ru": "Выберите ваш курс",
        },
        "options": [
            {"id": "1", "uz": "1", "ru": "1"},
            {"id": "2", "uz": "2", "ru": "2"},
            {"id": "3", "uz": "3", "ru": "3"},
            {"id": "4_5", "uz": "4-5", "ru": "4-5"},
        ],
        "accepted": {"4_5"},
    },
    "education_form": {
        "state": Form.education_form,
        "next": None,  # navbatdagi bosqich - CV so'rash
        "sheet_column": "Ta'lim shakli javobi",
        "reject_label": {"uz": "Ta'lim shakli", "ru": "Форма обучения"},
        "question": {
            "uz": "Ta'lim shaklingizni ko'rsating",
            "ru": "Укажите вашу форму обучения",
        },
        "options": [
            {"id": "kunduzgi", "uz": "Kunduzgi", "ru": "Очная"},
            {"id": "sirtqi", "uz": "Sirtqi", "ru": "Заочная"},
            {"id": "kechki", "uz": "Kechki", "ru": "Вечерняя"},
            {"id": "masofaviy", "uz": "Masofaviy", "ru": "Дистанционная"},
        ],
        "accepted": None,  # bu savol filtrlash uchun emas - hamma javob "mos"
    },
}

# FSM state string ("Form:age") -> savol kaliti ("age") - callback handlerda
# joriy holatni tez topish uchun.
STATE_KEY_MAP = {QUESTIONS[key]["state"].state: key for key in QUESTION_ORDER}


def get_option(question_key: str, option_id: str) -> dict | None:
    for option in QUESTIONS[question_key]["options"]:
        if option["id"] == option_id:
            return option
    return None


def is_accepted(question_key: str, option_id: str) -> bool:
    accepted = QUESTIONS[question_key]["accepted"]
    return accepted is None or option_id in accepted
