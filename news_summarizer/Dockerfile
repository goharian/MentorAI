# בסיס: תמונת פייתון רשמית
FROM python:3.11-slim

# הגדרת משתני סביבה כדי למנוע יצירת קבצי .pyc
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# הגדרת ספריית עבודה
WORKDIR /usr/src/app

# הוספת ספריית העבודה ל-PYTHONPATH
ENV PYTHONPATH=/usr/src/app

# התקנת דרישות מערכת (לצורך psycopg2)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    # מחיקת קבצים זמניים כדי להקטין את גודל האימג'
    && rm -rf /var/lib/apt/lists/*

# העתקת קובץ הדרישות והתקנתן
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת כל קבצי הפרויקט לתוך הקונטיינר
COPY . .

# הגדרת נקודת הכניסה (Entrypoint)
# נשתמש ב-gunicorn כ-WSGI Server בסביבת ייצור, אבל כרגע נשתמש בשרת המובנה של Django.
# נגדיר את פקודת ההפעלה ב-docker-compose