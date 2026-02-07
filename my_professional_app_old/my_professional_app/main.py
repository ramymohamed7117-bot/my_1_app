# main.py

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from database.connection import create_tables
from views.customers_view import CustomersView

class App(ttk.Window):
    def __init__(self):
        # <-- تغيير الثيم إلى "superhero" للتصميم الداكن
        super().__init__(themename="superhero")
        
        self.title("===== إصدار جديد تم اختباره =====")
        self.geometry("1350x800")
        
        create_tables()
        self._create_widgets()

    def _create_widgets(self):
        # ========== إطار العنوان العلوي بتصميم جديد ==========
        header_frame = ttk.Frame(self, bootstyle="primary", padding=(20, 15))
        header_frame.pack(fill=X)

        title_container = ttk.Frame(header_frame)
        title_container.pack(side=RIGHT, fill=X, expand=True)

        main_title = ttk.Label(
            title_container, 
            text="قسم خدمة العملاء",
            font=("Segoe UI", 26, "bold"),
            bootstyle="inverse-primary"
        )
        main_title.pack(anchor=W)

        subtitle = ttk.Label(
            title_container,
            text="تسجيل العملاء واعمال الصيانة",
            font=("Segoe UI", 14),
            bootstyle="inverse-secondary" # لون مختلف للعنوان الفرعي
        )
        subtitle.pack(anchor=W)
        
        # ========== المحتوى الرئيسي مع خلفية مميزة ==========
        # إطار بخلفية داكنة قليلاً لإعطاء عمق للواجهة
        main_container = ttk.Frame(self, bootstyle="dark", padding=20)
        main_container.pack(fill=BOTH, expand=True)
        
        customers_screen = CustomersView(main_container, self)
        customers_screen.pack(fill=BOTH, expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()