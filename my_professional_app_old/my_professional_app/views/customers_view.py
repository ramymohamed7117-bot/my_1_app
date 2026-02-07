# views/customers_view.py

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from services import customer_service

class CustomersView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_customer_id = None
        
        # خطوط وأحجام موحدة
        self.title_font = ("Segoe UI", 16, "bold")
        self.label_font = ("Segoe UI", 12)
        self.entry_font = ("Segoe UI", 11)
        
        self._create_widgets()
        self._populate_tree()

    def _create_widgets(self):
        """دالة لإنشاء وتنظيم كل عناصر الواجهة"""
        
        # --- الإطار الرئيسي للشاشة ---
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True)

        # --- الإطار الأيمن (النموذج والأزرار) بتصميم جديد ---
        # إطار مميز بخلفية مختلفة
        right_container = ttk.Frame(main_container, bootstyle="secondary", padding=25)
        right_container.pack(side=RIGHT, fill=Y, padx=(0, 15))
        
        # عنوان النموذج
        ttk.Label(
            right_container, 
            text="📝 نموذج البيانات", 
            font=self.title_font,
            bootstyle="inverse-secondary"
        ).pack(pady=(0, 20))
        
        # حقول الإدخال
        self._create_input_fields(right_container)
        
        # فاصل بصري
        ttk.Separator(right_container, orient='horizontal').pack(fill=X, pady=20)
        
        # الأزرار
        self._create_action_buttons(right_container)

        # --- الإطار الأيسر (الجدول والبحث) ---
        left_container = ttk.Frame(main_container, padding=(15, 0, 0, 0))
        left_container.pack(side=LEFT, fill=BOTH, expand=True)

        # شريط البحث
        self._create_search_bar(left_container)
        
        # الجدول
        self._create_treeview(left_container)

    def _create_input_fields(self, parent):
        """إنشاء حقول الإدخال"""
        fields = [
            ("الاسم:", "name_entry"),
            ("العنوان:", "address_entry"),
            ("الهاتف:", "phone_entry")
        ]
        
        for i, (label_text, attr_name) in enumerate(fields):
            ttk.Label(parent, text=label_text, font=self.label_font).grid(row=i, column=0, sticky=W, pady=12)
            entry = ttk.Entry(parent, font=self.entry_font, width=30)
            entry.grid(row=i, column=1, pady=12, padx=(10, 0))
            setattr(self, attr_name, entry)

    def _create_action_buttons(self, parent):
        """إنشاء أزرار الإجراءات"""
        btn_style = {"font": ("Segoe UI", 11, "bold"), "padding": (10, 12)}
        
        ttk.Button(parent, text="💾 حفظ عميل جديد", bootstyle=SUCCESS, command=self._save_customer, **btn_style).pack(fill=X, pady=5)
        ttk.Button(parent, text="✏️ تعديل البيانات", bootstyle=INFO, command=self._update_customer, **btn_style).pack(fill=X, pady=5)
        ttk.Button(parent, text="🗑️ حذف العميل", bootstyle=(DANGER, OUTLINE), command=self._delete_customer, **btn_style).pack(fill=X, pady=5)
        ttk.Button(parent, text="🧹 مسح الحقول", bootstyle=SECONDARY, command=self._clear_form, **btn_style).pack(fill=X, pady=5)

    def _create_search_bar(self, parent):
        """إنشاء شريط البحث"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(search_frame, text="🔍", font=("Segoe UI", 14)).pack(side=RIGHT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=self.entry_font)
        search_entry.pack(side=RIGHT, fill=X, expand=True)

    def _create_treeview(self, parent):
        """إنشاء الجدول"""
        # إطار للجدول بخلفية مميزة
        table_container = ttk.Frame(parent, bootstyle="primary", padding=10)
        table_container.pack(fill=BOTH, expand=True)
        
        columns = ("id", "name", "address", "phone")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", bootstyle="dark")
        
        # إعداد الأعمدة
        self.tree.heading("id", text="الرقم", anchor=CENTER)
        self.tree.heading("name", text="الاسم الكامل", anchor=W)
        self.tree.heading("address", text="العنوان", anchor=W)
        self.tree.heading("phone", text="رقم الهاتف", anchor=CENTER)
        
        self.tree.column("id", width=70, anchor=CENTER)
        self.tree.column("name", width=200, anchor=W)
        self.tree.column("address", width=280, anchor=W)
        self.tree.column("phone", width=140, anchor=CENTER)
        
        # زيادة ارتفاع الصفوف
        self.tree.configure(rowheight=30)

        scrollbar = ttk.Scrollbar(table_container, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ========== دوال المنطق (لم تتغير) ==========

    def _populate_tree(self, customers_list=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if customers_list is None:
            customers_list = customer_service.get_all_customers()
        for customer in customers_list:
            self.tree.insert("", END, values=customer)

    def _on_tree_select(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        selected_item = selected_items[0]
        customer_data = self.tree.item(selected_item, 'values')
        self.selected_customer_id = customer_data[0]
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, customer_data[1])
        self.address_entry.delete(0, tk.END)
        self.address_entry.insert(0, customer_data[2])
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, customer_data[3])

    def _save_customer(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "حقل الاسم مطلوب!", parent=self)
            return
        if customer_service.create_customer(name, self.address_entry.get(), self.phone_entry.get()):
            messagebox.showinfo("نجاح", "تم إضافة العميل بنجاح!", parent=self)
            self._clear_form()
            self._populate_tree()
        else:
            messagebox.showerror("خطأ", "فشل في إضافة العميل.", parent=self)

    def _update_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل للتعديل.", parent=self)
            return
        if customer_service.update_customer(self.selected_customer_id, self.name_entry.get(), self.address_entry.get(), self.phone_entry.get()):
            messagebox.showinfo("نجاح", "تم تحديث بيانات العميل بنجاح!", parent=self)
            self._clear_form()
            self._populate_tree()
        else:
            messagebox.showerror("خطأ", "فشل في تحديث بيانات العميل.", parent=self)

    def _delete_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عميل للحذف.", parent=self)
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا العميل؟", parent=self):
            if customer_service.delete_customer(self.selected_customer_id):
                messagebox.showinfo("نجاح", "تم حذف العميل بنجاح!", parent=self)
                self._clear_form()
                self._populate_tree()
            else:
                messagebox.showerror("خطأ", "فشل في حذف العميل.", parent=self)

    def _clear_form(self):
        self.selected_customer_id = None
        self.name_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def _on_search(self, *args):
        search_term = self.search_var.get().lower()
        all_customers = customer_service.get_all_customers()
        filtered_customers = [
            customer for customer in all_customers
            if search_term in customer[1].lower() or 
               search_term in customer[2].lower() or 
               search_term in customer[3].lower()
        ]
        self._populate_tree(filtered_customers)