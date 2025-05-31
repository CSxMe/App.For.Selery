"""PDF Invoice Generation using FPDF2."""

from fpdf import FPDF
from datetime import datetime
import os
import arabic_reshaper
from bidi.algorithm import get_display

# إعدادات الخطوط
FONT_ARABIC = 'Arial'  # خط يدعم العربية (متوفر في ويندوز وماك)
FONT_DEFAULT = 'Helvetica'

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', lang='en', translations=None):
        super().__init__(orientation, unit, format)
        self.current_lang = lang
        self.translations = translations or {}
        self.set_auto_page_break(auto=True, margin=15)
        self.set_font(FONT_DEFAULT, size=10)
        
        if lang == 'ar':
            self.set_rtl(True)
            self.set_doc_option('core_fonts_encoding', 'utf-8')

    def process_text(self, text):
        """معالجة النصوص العربية"""
        if self.current_lang == 'ar':
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        return text

    def header(self):
        self.set_font(FONT_ARABIC if self.current_lang == 'ar' else FONT_DEFAULT, 'B', 15)
        title = self.process_text(self.tr("invoice_title"))
        self.cell(0, 10, title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(FONT_ARABIC if self.current_lang == 'ar' else FONT_DEFAULT, 'I', 8)
        footer_text = self.process_text(self.tr("footer_text"))
        page_num_text = f"{self.tr('page_num')} {self.page_no()}/{{nb}}"
        
        if self.current_lang == 'ar':
            self.cell(0, 10, page_num_text, 0, 0, 'L')
            self.cell(0, 10, footer_text, 0, 0, 'R')
        else:
            self.cell(0, 10, footer_text, 0, 0, 'L')
            self.cell(0, 10, page_num_text, 0, 0, 'R')

    def tr(self, key):
        """ترجمة النصوص"""
        return self.process_text(self.translations.get(key, key))

    def add_invoice_details(self, invoice_data):
        self.set_font(FONT_ARABIC if self.current_lang == 'ar' else FONT_DEFAULT, '', 10)
        invoice_num_text = f"{self.tr('invoice_number')} {invoice_data['sale_id']}"
        
        try:
            sale_date = datetime.fromisoformat(invoice_data['sale_date'].split('.')[0])
            date_text = f"{self.tr('date_label')} {sale_date.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            date_text = f"{self.tr('date_label')} {invoice_data['sale_date']}"
        
        align = 'R' if self.current_lang == 'ar' else 'L'
        self.cell(0, 7, invoice_num_text, 0, 1, align)
        self.cell(0, 7, date_text, 0, 1, align)
        self.ln(10)

    def add_items_table(self, items):
        self.set_font(FONT_ARABIC if self.current_lang == 'ar' else FONT_DEFAULT, 'B', 10)
        page_width = self.w - self.l_margin - self.r_margin
        col_widths = [page_width*0.45, page_width*0.15, page_width*0.20, page_width*0.20]
        line_height = self.font_size * 2
        
        # عناوين الأعمدة
        headers = [
            self.tr("item_header"),
            self.tr("quantity_short"),
            self.tr("price_header"),
            self.tr("total_label")
        ]
        
        if self.current_lang == 'ar':
            headers.reverse()
            col_widths.reverse()
        
        for i, header in enumerate(headers):
            self.cell(col_widths[i], line_height, header, border=1, align='C')
        self.ln(line_height)
        
        # محتوى الجدول
        self.set_font(FONT_ARABIC if self.current_lang == 'ar' else FONT_DEFAULT, '', 10)
        for item in items:
            name = self.process_text(str(item.get('name', '')))
            qty = str(item.get('quantity_sold', ''))
            price = f"{item.get('price_at_sale', 0):.2f}"
            total = f"{item.get('quantity_sold', 0) * item.get('price_at_sale', 0):.2f}"
            
            if self.current_lang == 'ar':
                row = [total, price, qty, name]
            else:
                row = [name, qty, price, total]
            
            for i in range(4):
                self.cell(col_widths[i], line_height, row[i], border=1, align='C')
            self.ln(line_height)
        
        self.ln(5)

    def add_total(self, total_amount):
        self.set_font(FONT_ARABIC if self.current_lang == 'ar' else FONT_DEFAULT, 'B', 12)
        total_text = f"{self.tr('total_label')} {total_amount:.2f}"
        align = 'L' if self.current_lang == 'ar' else 'R'
        self.cell(0, 10, total_text, 0, 1, align)
        self.ln(5)

def generate_invoice_pdf(save_path, invoice_data, lang_translations, current_lang):
    """إنشاء ملف PDF للفاتورة"""
    try:
        pdf = PDF(lang=current_lang, translations=lang_translations)
        pdf.add_page()
        pdf.add_invoice_details(invoice_data)
        pdf.add_items_table(invoice_data.get('items', []))
        pdf.add_total(invoice_data.get('total_amount', 0))
        pdf.output(save_path)
        print(f"تم إنشاء الفاتورة بنجاح: {save_path}")
        return True
    except Exception as e:
        print(f"خطأ في إنشاء الفاتورة: {e}")
        return False

# مثال للاستخدام
if __name__ == '__main__':
    # بيانات عربية
    ar_translations = {
        "invoice_title": "فاتورة",
        "invoice_number": "رقم الفاتورة",
        "date_label": "التاريخ",
        "item_header": "الصنف",
        "quantity_short": "الكمية",
        "price_header": "السعر",
        "total_label": "الإجمالي",
        "footer_text": "شكراً لتعاملكم معنا",
        "page_num": "صفحة"
    }
    
    # بيانات إنجليزية
    en_translations = {
        "invoice_title": "Invoice",
        "invoice_number": "Invoice Number",
        "date_label": "Date",
        "item_header": "Item",
        "quantity_short": "Qty",
        "price_header": "Price",
        "total_label": "Total",
        "footer_text": "Thank you for your business",
        "page_num": "Page"
    }
    
    # بيانات الفاتورة
    invoice_data = {
        "sale_id": 1001,
        "sale_date": datetime.now().isoformat(),
        "total_amount": 1250.75,
        "items": [
            {"name": "هاتف ذكي", "quantity_sold": 1, "price_at_sale": 1000},
            {"name": "حافظة", "quantity_sold": 2, "price_at_sale": 125.375}
        ]
    }
    
    # إنشاء الفاتورة العربية
    generate_invoice_pdf("invoice_ar.pdf", invoice_data, ar_translations, 'ar')
    
    # إنشاء الفاتورة الإنجليزية
    generate_invoice_pdf("invoice_en.pdf", invoice_data, en_translations, 'en')
