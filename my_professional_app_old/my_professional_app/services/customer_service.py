# services/customer_service.py

from database.connection import get_connection

def create_customer(name, address, phone):
    """
    إضافة عميل جديد إلى قاعدة البيانات.
    
    Args:
        name (str): اسم العميل.
        address (str): عنوان العميل.
        phone (str): هاتف العميل.
        
    Returns:
        int: معرّف العميل الجديد (ID) في حال النجاح، أو None في حال الفشل.
    """
    conn = get_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name, address, phone) VALUES (?, ?, ?)",
            (name, address, phone)
        )
        conn.commit()
        # إرجاع معرّف العميل الذي تم إنشاؤه حديثًا
        return cursor.lastrowid
    except Exception as e:
        print(f"خطأ أثناء إضافة العميل: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_all_customers():
    """
    جلب قائمة بكل العملاء من قاعدة البيانات.
    
    Returns:
        list: قائمة من الـ tuples، كل tuple يمثل عميلاً.
    """
    conn = get_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, address, phone, created_at FROM customers ORDER BY id DESC")
        return cursor.fetchall()
    except Exception as e:
        print(f"خطأ أثناء جلب العملاء: {e}")
        return []
    finally:
        conn.close()

def get_customer_by_id(customer_id):
    """
    جلب بيانات عميل محدد باستخدام معرّفه.
    
    Args:
        customer_id (int): معرّف العميل.
        
    Returns:
        tuple: بيانات العميل، أو None إذا لم يتم العثور عليه.
    """
    conn = get_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"خطأ أثناء جلب العميل: {e}")
        return None
    finally:
        conn.close()

def update_customer(customer_id, name, address, phone):
    """
    تحديث بيانات عميل موجود.
    
    Args:
        customer_id (int): معرّف العميل.
        name (str): الاسم الجديد.
        address (str): العنوان الجديد.
        phone (str): الهاتف الجديد.
        
    Returns:
        bool: True في حال النجاح، False في حال الفشل.
    """
    conn = get_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE customers SET name = ?, address = ?, phone = ? WHERE id = ?",
            (name, address, phone, customer_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"خطأ أثناء تحديث العميل: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_customer(customer_id):
    """
    حذف عميل من قاعدة البيانات.
    
    Args:
        customer_id (int): معرّف العميل المراد حذفه.
        
    Returns:
        bool: True في حال النجاح، False في حال الفشل.
    """
    conn = get_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"خطأ أثناء حذف العميل: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
