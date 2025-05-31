
"""Main application file for the Phone Store Manager."""

import sys
import json
import os
import sqlite3
from datetime import datetime, timedelta, time # Added time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QStatusBar, QMenuBar, QGridLayout, QLineEdit, 
    QTableWidget, QHeaderView, QComboBox, QSpinBox, QMessageBox, QFileDialog, 
    QTableWidgetItem, QAbstractItemView, QDialog, QFormLayout, QDialogButtonBox,
    QDoubleSpinBox, QSizePolicy, QSpacerItem, QDateEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QAction, QFont

# Import database functions
import database as db
# Import PDF generation function
from pdf_generator import generate_invoice_pdf

class ProductDialog(QDialog):
    """Dialog for adding or editing a product."""
    def __init__(self, parent=None, product_data=None, translations=None, current_lang="en"):
        super().__init__(parent)
        self.translations = translations
        self.current_lang = current_lang
        self.product_data = product_data

        self.setWindowTitle(self.tr("add_product_button") if product_data is None else self.tr("edit_product_button"))

        self.layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.original_price_spin = QDoubleSpinBox()
        self.original_price_spin.setRange(0, 999999.99)
        self.original_price_spin.setDecimals(2)
        self.selling_price_spin = QDoubleSpinBox()
        self.selling_price_spin.setRange(0, 999999.99)
        self.selling_price_spin.setDecimals(2)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)

        self.layout.addRow(self.tr("product_name_label"), self.name_edit)
        self.layout.addRow(self.tr("original_price_label"), self.original_price_spin)
        self.layout.addRow(self.tr("selling_price_label"), self.selling_price_spin)
        self.layout.addRow(self.tr("quantity_label"), self.quantity_spin)

        if product_data:
            self.name_edit.setText(product_data["name"])
            self.original_price_spin.setValue(product_data["original_price"])
            self.selling_price_spin.setValue(product_data["selling_price"])
            self.quantity_spin.setValue(product_data["quantity"])

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # Translate buttons
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("save_button"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("cancel_button"))

        self.layout.addWidget(self.button_box)
        self.update_layout_direction()

    def tr(self, key):
        """Translate a key using the current language."""
        # Use parent's tr method if available
        if hasattr(self.parent(), 'tr'):
            return self.parent().tr(key)
        # Fallback if no parent or parent has no tr
        if self.translations and self.current_lang in self.translations:
            return self.translations[self.current_lang].get(key, key)
        return key

    def update_layout_direction(self):
        if self.current_lang == 'ar':
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "original_price": self.original_price_spin.value(),
            "selling_price": self.selling_price_spin.value(),
            "quantity": self.quantity_spin.value()
        }

class PhoneStoreApp(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.current_lang = "en" # Default language
        self.translations = self.load_translations()
        self.current_cart = [] # List to hold items for the current sale
        self.available_products = [] # Cache available products for sales tab
        db.init_db() # Initialize database
        self.init_ui()

    def load_translations(self):
        translations = {}
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        lang_dir = os.path.join(base_path, 'lang')
        print(f"Looking for translation files in: {lang_dir}")

        for lang_code in ["en", "fr", "ar"]:
            try:
                filepath = os.path.join(lang_dir, f"{lang_code}.json")
                if not os.path.exists(filepath):
                    print(f"Warning: File not found at {filepath}")
                    translations[lang_code] = {}
                    continue
                with open(filepath, 'r', encoding='utf-8') as f:
                    translations[lang_code] = json.load(f)
                    print(f"Loaded translations for '{lang_code}'")
            except Exception as e:
                 print(f"An error occurred loading '{lang_code}': {e}")
                 translations[lang_code] = {}
        return translations

    def tr(self, key):
        return self.translations.get(self.current_lang, {}).get(key, key)

    def init_ui(self):
        self.setWindowTitle(self.tr("app_title"))
        self.setGeometry(100, 100, 1100, 750) # Increased size slightly

        self.setup_menu()
        self.setup_tabs()
        self.setup_status_bar()

        self.retranslate_ui() # Apply initial translations
        self.load_inventory_data() # Load initial data for inventory tab
        self.update_available_products() # Load products for sales tab dropdown

    def setup_menu(self):
        self.menubar = self.menuBar()
        self.language_menu = self.menubar.addMenu(self.tr("menu_language"))

        self.en_action = QAction(self.tr("lang_english"), self)
        self.en_action.triggered.connect(lambda: self.change_language("en"))
        self.language_menu.addAction(self.en_action)

        self.fr_action = QAction(self.tr("lang_french"), self)
        self.fr_action.triggered.connect(lambda: self.change_language("fr"))
        self.language_menu.addAction(self.fr_action)

        self.ar_action = QAction(self.tr("lang_arabic"), self)
        self.ar_action.triggered.connect(lambda: self.change_language("ar"))
        self.language_menu.addAction(self.ar_action)

    def setup_tabs(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.inventory_tab = QWidget()
        self.sales_tab = QWidget()
        self.reports_tab = QWidget() # New reports tab

        self.tabs.addTab(self.inventory_tab, self.tr("tab_inventory"))
        self.tabs.addTab(self.sales_tab, self.tr("tab_sales"))
        self.tabs.addTab(self.reports_tab, self.tr("tab_reports")) # Add the new tab

        self.setup_inventory_ui()
        self.setup_sales_ui()
        self.setup_reports_ui() # Setup the UI for the new tab

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.clock_label = QLabel()
        self.status_bar.addPermanentWidget(self.clock_label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        self.footer_label = QLabel(self.tr("footer_text"))
        self.status_bar.addPermanentWidget(self.footer_label)
        
        # Use addWidget with stretch factor for proper spacing
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_bar.addWidget(spacer, 1)
        self.status_bar.addWidget(self.clock_label)
        self.status_bar.addWidget(self.footer_label)

    def setup_inventory_ui(self):
        layout = QVBoxLayout(self.inventory_tab)
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inventory_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.inventory_table.verticalHeader().setVisible(False)
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.inventory_table.hideColumn(0)
        layout.addWidget(self.inventory_table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton()
        self.edit_button = QPushButton()
        self.delete_button = QPushButton()
        self.add_button.clicked.connect(self.add_product_dialog)
        self.edit_button.clicked.connect(self.edit_product_dialog)
        self.delete_button.clicked.connect(self.delete_product_action)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def load_inventory_data(self):
        self.inventory_table.setRowCount(0)
        products = db.get_all_products()
        self.inventory_table.setRowCount(len(products))
        for row_idx, product in enumerate(products):
            self.inventory_table.setItem(row_idx, 0, QTableWidgetItem(str(product["id"]))) # Hidden ID
            self.inventory_table.setItem(row_idx, 1, QTableWidgetItem(product["name"]))
            self.inventory_table.setItem(row_idx, 2, QTableWidgetItem(f"{product['original_price']:.2f}"))
            self.inventory_table.setItem(row_idx, 3, QTableWidgetItem(f"{product['selling_price']:.2f}"))
            self.inventory_table.setItem(row_idx, 4, QTableWidgetItem(str(product["quantity"]))) 
        self.inventory_table.resizeColumnsToContents()
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        self.update_available_products() # Refresh products for sales tab

    def update_available_products(self):
        self.available_products = db.get_all_products()
        # Update the product selection dropdown in the sales tab
        if hasattr(self, 'product_combo'):
            current_selection_data = self.product_combo.currentData()
            self.product_combo.clear()
            selected_index = -1
            for index, product in enumerate(self.available_products):
                if product['quantity'] > 0:
                    display_text = f"{product['name']} ({self.tr('quantity_short')}: {product['quantity']}, {self.tr('price_short')}: {product['selling_price']:.2f})"
                    self.product_combo.addItem(display_text, userData=product)
                    if current_selection_data and product['id'] == current_selection_data['id']:
                        selected_index = self.product_combo.count() - 1
            self.product_combo.setCurrentIndex(selected_index)
            if selected_index == -1:
                 self.product_combo.setCurrentIndex(-1) # Ensure placeholder if selection gone
                 self.quantity_spin_sales.setRange(1, 1)
                 self.quantity_spin_sales.setEnabled(False)
            else:
                 self.update_quantity_spin_limit() # Update limit for restored selection

    def add_product_dialog(self):
        dialog = ProductDialog(self, translations=self.translations, current_lang=self.current_lang)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"] or data["selling_price"] <= 0:
                 QMessageBox.warning(self, self.tr("invalid_input_title"), self.tr("invalid_input_text"))
                 return
            success = db.add_product(data["name"], data["original_price"], data["selling_price"], data["quantity"])
            if success:
                self.load_inventory_data()
            else:
                QMessageBox.critical(self, self.tr("error_title"), self.tr("db_error_text_add"))

    def edit_product_dialog(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        selected_row = selected_rows[0].row()
        product_id = int(self.inventory_table.item(selected_row, 0).text())
        product_data = db.get_product_by_id(product_id) # Fetch fresh data
        if not product_data:
             QMessageBox.critical(self, self.tr("error_title"), self.tr("db_error_fetch"))
             return

        dialog = ProductDialog(self, product_data=product_data, translations=self.translations, current_lang=self.current_lang)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"] or data["selling_price"] <= 0:
                 QMessageBox.warning(self, self.tr("invalid_input_title"), self.tr("invalid_input_text"))
                 return
            success = db.update_product(product_id, data["name"], data["original_price"], data["selling_price"], data["quantity"])
            if success:
                self.load_inventory_data()
            else:
                QMessageBox.critical(self, self.tr("error_title"), self.tr("db_error_text_update"))

    def delete_product_action(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        selected_row = selected_rows[0].row()
        product_id = int(self.inventory_table.item(selected_row, 0).text())
        product_name = self.inventory_table.item(selected_row, 1).text()

        reply = QMessageBox.question(self, self.tr("confirm_delete_title"), 
                                     self.tr("confirm_delete_text") + f"\n\n{product_name}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success = db.delete_product(product_id)
            if success:
                self.load_inventory_data()
            else:
                 QMessageBox.critical(self, self.tr("error_title"), self.tr("db_error_text_delete"))

    def setup_sales_ui(self):
        main_layout = QHBoxLayout(self.sales_tab)
        
        # Left side: Product selection and adding to cart
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(400)

        # Product Selection
        product_selection_layout = QHBoxLayout()
        self.product_label = QLabel(self.tr("select_product_label"))
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.update_quantity_spin_limit)
        product_selection_layout.addWidget(self.product_label)
        product_selection_layout.addWidget(self.product_combo)
        left_layout.addLayout(product_selection_layout)

        # Quantity Selection
        quantity_layout = QHBoxLayout()
        self.quantity_label_sales = QLabel(self.tr("quantity_label"))
        self.quantity_spin_sales = QSpinBox()
        self.quantity_spin_sales.setRange(1, 1) # Default range, updated on product selection
        self.quantity_spin_sales.setEnabled(False) # Disabled initially
        quantity_layout.addWidget(self.quantity_label_sales)
        quantity_layout.addWidget(self.quantity_spin_sales)
        left_layout.addLayout(quantity_layout)

        # Add to Cart Button
        self.add_to_cart_button = QPushButton(self.tr("add_to_cart_button"))
        self.add_to_cart_button.clicked.connect(self.add_item_to_cart)
        left_layout.addWidget(self.add_to_cart_button)
        left_layout.addStretch()

        # Right side: Cart display and checkout
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Cart Table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5) # Name, Price, Quantity, Total, ProductID (Hidden)
        self.cart_table.setHorizontalHeaderLabels([self.tr("item_header"), self.tr("price_header"), self.tr("quantity_label"), self.tr("total_label"), "ProductID"])
        self.cart_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.hideColumn(4) # Hide ProductID
        right_layout.addWidget(self.cart_table)

        # Total Amount Display
        total_layout = QHBoxLayout()
        self.total_amount_label = QLabel(f"{self.tr('total_label')} 0.00")
        font = self.total_amount_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.total_amount_label.setFont(font)
        total_layout.addStretch()
        total_layout.addWidget(self.total_amount_label)
        right_layout.addLayout(total_layout)

        # Checkout Button
        self.process_sale_button = QPushButton(self.tr("process_sale_button"))
        self.process_sale_button.clicked.connect(self.process_sale)
        right_layout.addWidget(self.process_sale_button)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def update_quantity_spin_limit(self, index=-1): # Allow calling without index
        if index == -1: # If called without index, use current index
            index = self.product_combo.currentIndex()
            
        if index == -1:
            self.quantity_spin_sales.setRange(1, 1)
            self.quantity_spin_sales.setEnabled(False)
            return
        
        selected_product = self.product_combo.itemData(index)
        if selected_product:
            max_qty = selected_product.get('quantity', 0)
            if max_qty > 0:
                self.quantity_spin_sales.setRange(1, max_qty)
                self.quantity_spin_sales.setEnabled(True)
            else:
                self.quantity_spin_sales.setRange(1, 1)
                self.quantity_spin_sales.setEnabled(False)
        else:
            self.quantity_spin_sales.setRange(1, 1)
            self.quantity_spin_sales.setEnabled(False)

    def add_item_to_cart(self):
        selected_index = self.product_combo.currentIndex()
        if selected_index == -1:
            QMessageBox.warning(self, self.tr("selection_error_title"), self.tr("selection_error_text"))
            return

        product_data = self.product_combo.itemData(selected_index)
        quantity_to_add = self.quantity_spin_sales.value()

        # Check if item already in cart
        existing_row = -1
        for row in range(self.cart_table.rowCount()):
            if int(self.cart_table.item(row, 4).text()) == product_data['id']:
                existing_row = row
                break

        current_cart_qty = 0
        if existing_row != -1:
            current_cart_qty = int(self.cart_table.item(existing_row, 2).text())

        if current_cart_qty + quantity_to_add > product_data['quantity']:
            QMessageBox.warning(self, self.tr("quantity_error_title"), self.tr("quantity_error_text"))
            return

        if existing_row != -1:
            # Update existing row
            new_qty = current_cart_qty + quantity_to_add
            self.cart_table.item(existing_row, 2).setText(str(new_qty))
            item_total = new_qty * product_data['selling_price']
            self.cart_table.item(existing_row, 3).setText(f"{item_total:.2f}")
        else:
            # Add new row
            row_position = self.cart_table.rowCount()
            self.cart_table.insertRow(row_position)
            item_total = quantity_to_add * product_data['selling_price']
            self.cart_table.setItem(row_position, 0, QTableWidgetItem(product_data['name']))
            self.cart_table.setItem(row_position, 1, QTableWidgetItem(f"{product_data['selling_price']:.2f}"))
            self.cart_table.setItem(row_position, 2, QTableWidgetItem(str(quantity_to_add)))
            self.cart_table.setItem(row_position, 3, QTableWidgetItem(f"{item_total:.2f}"))
            self.cart_table.setItem(row_position, 4, QTableWidgetItem(str(product_data['id']))) # Hidden ID

        self.update_cart_total()
        self.cart_table.resizeColumnsToContents()
        self.cart_table.horizontalHeader().setStretchLastSection(True)

    def update_cart_total(self):
        total = 0.0
        for row in range(self.cart_table.rowCount()):
            try:
                total += float(self.cart_table.item(row, 3).text())
            except (ValueError, TypeError):
                pass # Ignore if cell is empty or invalid
        self.total_amount_label.setText(f"{self.tr('total_label')} {total:.2f}")

    def process_sale(self):
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, self.tr("empty_cart_title"), self.tr("empty_cart_text"))
            return

        items_to_record = []
        total_sale_price = 0.0
        for row in range(self.cart_table.rowCount()):
            product_id = int(self.cart_table.item(row, 4).text())
            quantity = int(self.cart_table.item(row, 2).text())
            selling_price = float(self.cart_table.item(row, 1).text())
            items_to_record.append({
                'id': product_id,
                'quantity': quantity,
                'selling_price': selling_price
            })
            total_sale_price += selling_price * quantity

        # Record the sale in the database
        sale_id = db.record_sale(items_to_record, total_sale_price)

        if sale_id:
            QMessageBox.information(self, self.tr("sale_success_title"), f"{self.tr('sale_success_text')} {sale_id}")
            
            # Generate PDF Invoice
            self.generate_pdf_invoice(sale_id)

            # Clear cart and update inventory/product list
            self.cart_table.setRowCount(0)
            self.update_cart_total()
            self.load_inventory_data() # Reload inventory to reflect updated quantities
            # self.update_available_products() # This is called within load_inventory_data
        else:
            QMessageBox.critical(self, self.tr("error_title"), self.tr("db_error_text_sale"))

    def generate_pdf_invoice(self, sale_id):
        sale_details = db.get_sale_details(sale_id)
        if not sale_details or not sale_details.get("sale_info"):
            QMessageBox.critical(self, self.tr("error_title"), self.tr("pdf_error_fetch_details"))
            return

        # Prepare data structure for PDF generator
        invoice_data = {
            "sale_id": sale_details["sale_info"]["id"],
            "sale_date": sale_details["sale_info"]["sale_date"],
            "total_amount": sale_details["sale_info"]["total_amount"],
            "items": sale_details["items"] # Already includes name, quantity_sold, price_at_sale
        }
        
        # Get translations for the current language for the PDF
        pdf_translations = self.translations.get(self.current_lang, {})

        # Prompt user for save location
        default_filename = f"invoice_{sale_id}.pdf"
        save_path, _ = QFileDialog.getSaveFileName(self, self.tr("save_invoice_title"), default_filename, "PDF Files (*.pdf)")

        if save_path:
            try:
                success = generate_invoice_pdf(save_path, invoice_data, pdf_translations, self.current_lang)
                if success:
                     QMessageBox.information(self, self.tr("pdf_success_title"), f"{self.tr('pdf_success_text')}\n{save_path}")
                else:
                     QMessageBox.critical(self, self.tr("error_title"), self.tr("pdf_error_generate"))
            except Exception as e:
                QMessageBox.critical(self, self.tr("error_title"), f"{self.tr('pdf_error_generate')}\nError: {e}")
                print(f"Error calling generate_invoice_pdf: {e}")
                import traceback
                traceback.print_exc()

    # --- Reports Tab UI --- 
    def setup_reports_ui(self):
        layout = QVBoxLayout(self.reports_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Daily Report Section ---
        self.daily_group = QGroupBox(self.tr("report_daily_title")) # Made attribute
        daily_layout = QGridLayout(self.daily_group)

        self.daily_date_label = QLabel(self.tr("report_select_date"))
        self.daily_date_edit = QDateEdit(QDate.currentDate())
        self.daily_date_edit.setCalendarPopup(True)
        self.daily_date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.daily_report_button = QPushButton(self.tr("report_generate_button"))
        self.daily_report_button.clicked.connect(self.generate_daily_report)

        self.daily_sales_label = QLabel(f"{self.tr('report_total_sales')}: -")
        self.daily_profit_label = QLabel(f"{self.tr('report_total_profit')}: -")

        daily_layout.addWidget(self.daily_date_label, 0, 0)
        daily_layout.addWidget(self.daily_date_edit, 0, 1)
        daily_layout.addWidget(self.daily_report_button, 0, 2)
        daily_layout.addWidget(self.daily_sales_label, 1, 0, 1, 3)
        daily_layout.addWidget(self.daily_profit_label, 2, 0, 1, 3)
        daily_layout.setColumnStretch(1, 1) # Allow date edit to expand a bit

        layout.addWidget(self.daily_group)

        # --- Yearly Report Section ---
        self.yearly_group = QGroupBox(self.tr("report_yearly_title")) # Made attribute
        yearly_layout = QGridLayout(self.yearly_group)

        self.yearly_year_label = QLabel(self.tr("report_select_year"))
        self.yearly_year_spin = QSpinBox()
        self.yearly_year_spin.setRange(2000, QDate.currentDate().year() + 5) # Allow future years slightly
        self.yearly_year_spin.setValue(QDate.currentDate().year())

        self.yearly_report_button = QPushButton(self.tr("report_generate_button"))
        self.yearly_report_button.clicked.connect(self.generate_yearly_report)

        self.yearly_sales_label = QLabel(f"{self.tr('report_total_sales')}: -")
        self.yearly_profit_label = QLabel(f"{self.tr('report_total_profit')}: -")

        yearly_layout.addWidget(self.yearly_year_label, 0, 0)
        yearly_layout.addWidget(self.yearly_year_spin, 0, 1)
        yearly_layout.addWidget(self.yearly_report_button, 0, 2)
        yearly_layout.addWidget(self.yearly_sales_label, 1, 0, 1, 3)
        yearly_layout.addWidget(self.yearly_profit_label, 2, 0, 1, 3)
        yearly_layout.setColumnStretch(1, 1)

        layout.addWidget(self.yearly_group)

        layout.addStretch() # Push groups to the top

    # --- Report Generation Logic --- 
    def generate_daily_report(self):
        selected_qdate = self.daily_date_edit.date()
        # Convert QDate to datetime objects for start and end of day
        selected_dt = datetime(selected_qdate.year(), selected_qdate.month(), selected_qdate.day())
        start_of_day = datetime.combine(selected_dt.date(), time.min) # Midnight start
        end_of_day = datetime.combine(selected_dt.date(), time.max)   # End of day
        
        # Format for SQLite query (YYYY-MM-DD HH:MM:SS)
        start_date_str = start_of_day.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_of_day.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Generating daily report for: {selected_dt.date()} (Range: {start_date_str} to {end_date_str})")
        result = db.get_sales_and_profit_for_period(start_date_str, end_date_str)
        
        self.daily_sales_label.setText(f"{self.tr('report_total_sales')}: {result['total_sales']:.2f}")
        self.daily_profit_label.setText(f"{self.tr('report_total_profit')}: {result['total_profit']:.2f}")

    def generate_yearly_report(self):
        selected_year = self.yearly_year_spin.value()
        # Define start and end dates for the year
        start_of_year = datetime(selected_year, 1, 1, 0, 0, 0)
        end_of_year = datetime(selected_year, 12, 31, 23, 59, 59)
        
        # Format for SQLite query
        start_date_str = start_of_year.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_of_year.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Generating yearly report for: {selected_year} (Range: {start_date_str} to {end_date_str})")
        result = db.get_sales_and_profit_for_period(start_date_str, end_date_str)
        
        self.yearly_sales_label.setText(f"{self.tr('report_total_sales')}: {result['total_sales']:.2f}")
        self.yearly_profit_label.setText(f"{self.tr('report_total_profit')}: {result['total_profit']:.2f}")

    # --- Language and UI Update --- 
    def change_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code
            # Update layout direction first
            if lang_code == 'ar':
                self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                QApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            # Retranslate all UI elements
            self.retranslate_ui()
            # Reload data that might contain translatable elements (like dropdown)
            self.update_available_products()
            self.update_cart_total() # Update total label translation
            # Reset report labels as data needs regeneration for the new language context (if needed)
            self.daily_sales_label.setText(f"{self.tr('report_total_sales')}: -")
            self.daily_profit_label.setText(f"{self.tr('report_total_profit')}: -")
            self.yearly_sales_label.setText(f"{self.tr('report_total_sales')}: -")
            self.yearly_profit_label.setText(f"{self.tr('report_total_profit')}: -")
        else:
            print(f"Language '{lang_code}' not supported or translations not loaded.")

    def retranslate_ui(self):
        self.setWindowTitle(self.tr("app_title"))
        # Menu
        self.language_menu.setTitle(self.tr("menu_language"))
        self.en_action.setText(self.tr("lang_english"))
        self.fr_action.setText(self.tr("lang_french"))
        self.ar_action.setText(self.tr("lang_arabic"))
        # Tabs
        self.tabs.setTabText(0, self.tr("tab_inventory"))
        self.tabs.setTabText(1, self.tr("tab_sales"))
        self.tabs.setTabText(2, self.tr("tab_reports")) # Translate new tab
        # Inventory Tab
        self.inventory_table.setHorizontalHeaderLabels(["ID", self.tr("product_name_label"), self.tr("original_price_label"), self.tr("selling_price_label"), self.tr("quantity_label")])
        self.add_button.setText(self.tr("add_product_button"))
        self.edit_button.setText(self.tr("edit_product_button"))
        self.delete_button.setText(self.tr("delete_product_button"))
        # Sales Tab
        self.product_label.setText(self.tr("select_product_label"))
        self.quantity_label_sales.setText(self.tr("quantity_label"))
        self.add_to_cart_button.setText(self.tr("add_to_cart_button"))
        self.cart_table.setHorizontalHeaderLabels([self.tr("item_header"), self.tr("price_header"), self.tr("quantity_label"), self.tr("total_label"), "ProductID"])
        self.total_amount_label.setText(f"{self.tr('total_label')} {self.calculate_cart_total():.2f}") # Recalculate total with new label
        self.process_sale_button.setText(self.tr("process_sale_button"))
        # Reports Tab
        if hasattr(self, 'daily_group'): # Check if reports UI is initialized
            self.daily_group.setTitle(self.tr("report_daily_title"))
            self.daily_date_label.setText(self.tr("report_select_date"))
            self.daily_report_button.setText(self.tr("report_generate_button"))
            # Keep existing values, just update labels
            current_daily_sales = self.daily_sales_label.text().split(":")[-1].strip()
            current_daily_profit = self.daily_profit_label.text().split(":")[-1].strip()
            self.daily_sales_label.setText(f"{self.tr('report_total_sales')}: {current_daily_sales}")
            self.daily_profit_label.setText(f"{self.tr('report_total_profit')}: {current_daily_profit}")

            self.yearly_group.setTitle(self.tr("report_yearly_title"))
            self.yearly_year_label.setText(self.tr("report_select_year"))
            self.yearly_report_button.setText(self.tr("report_generate_button"))
            current_yearly_sales = self.yearly_sales_label.text().split(":")[-1].strip()
            current_yearly_profit = self.yearly_profit_label.text().split(":")[-1].strip()
            self.yearly_sales_label.setText(f"{self.tr('report_total_sales')}: {current_yearly_sales}")
            self.yearly_profit_label.setText(f"{self.tr('report_total_profit')}: {current_yearly_profit}")

        # Status Bar
        self.footer_label.setText(self.tr("footer_text"))
        # Force layout update for RTL/LTR changes
        self.inventory_tab.layout().update()
        self.sales_tab.layout().update()
        if hasattr(self, 'reports_tab'):
            self.reports_tab.layout().update()

    def calculate_cart_total(self):
        total = 0.0
        for row in range(self.cart_table.rowCount()):
            try:
                total += float(self.cart_table.item(row, 3).text())
            except (ValueError, TypeError):
                pass # Ignore if cell is empty or invalid
        return total

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.setText(now)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Set application font globally if needed, especially for Arabic
    # font = QFont("Arial", 12) # Example, choose appropriate font
    # app.setFont(font)
    main_win = PhoneStoreApp()
    main_win.show()
    sys.exit(app.exec())

