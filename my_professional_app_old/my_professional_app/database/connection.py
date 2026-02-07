# database/connection.py

import sqlite3
import os

# تحديد مسار قاعدة البيانات
# بهذه الطريقة، سيعمل الكود بغض النظر عن مكان تشغيله
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_connection():
    """
    هذه الدالة تقوم بإنشاء وإرجاع اتصال بقاعدة البيانات.
    إذا لم تكن قاعدة البيانات موجودة، سيتم إنشاؤها تلقائيًا.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # تمكين مفاتيح الخارجية (Foreign Keys) لقواعد البيانات المعقدة مستقبلاً
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

# دالة مساعدة لإنشاء الجداول (سنستخدمها مرة واحدة في البداية)
def create_tables():
    """
    هذه الدالة تقوم بإنشاء الجداول اللازمة في قاعدة البيانات إذا لم تكن موجودة.
    """
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    
    # جدول العملاء
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # يمكنك إضافة جداول أخرى هنا في المستقبل (مثل products, invoices)
    
    conn.commit()
    conn.close()
    print("تم إنشاء الجداول بنجاح (أو كانت موجودة مسبقًا).")
