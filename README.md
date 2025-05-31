# Phone Store Management Application

This application helps manage inventory, sales, and reports for a phone store. It features multilingual support (English, French, Arabic), offline data storage, PDF invoice generation, and sales/profit reporting.

## Features

*   **Inventory Management:** Add, edit, delete, and view phone models including name, original price, selling price, and quantity.
*   **Sales Processing:** Select products, specify quantities, and add them to a sales cart.
*   **Invoice Generation:** Process sales, automatically update inventory, and generate PDF invoices for each sale.
*   **Reporting:** View daily and yearly reports summarizing total sales and calculated profit for the selected period.
*   **Multilingual Interface:** Switch between English, French, and Arabic languages dynamically.
*   **Offline Operation:** All data (inventory, sales) is stored locally in a `store_data.db` SQLite database file within the application folder.
*   **Real-time Clock & Footer:** Displays the current time and a custom footer in the status bar.

## Requirements

*   **macOS:** Tested on macOS (should work on M1).
*   **Python 3:** Ensure Python 3 is installed. You can check by opening Terminal and typing `python3 --version`.
*   **pip:** Python's package installer, usually comes with Python 3. Check with `pip3 --version`.

## Installation and Setup

1.  **Download and Unzip:** Download the provided `phone_store_app.zip` file and unzip it to a location of your choice on your MacBook.
2.  **Open Terminal:** Navigate to the unzipped `phone_store_app` directory using the `cd` command in Terminal. For example:
    ```bash
    cd /path/to/your/unzipped/phone_store_app
    ```
3.  **(Recommended) Create and Activate a Virtual Environment:** It's best practice to create a separate environment for the application's dependencies. 
    *   Create the environment (run this command *outside* the `phone_store_app` folder, e.g., in your Downloads folder if that's where you unzipped it):
        ```bash
        python3 -m venv store_venv 
        ```
    *   Activate the environment:
        ```bash
        source store_venv/bin/activate
        ```
        *(You should see `(store_venv)` at the beginning of your terminal prompt)*
    *   Now, navigate *into* the `phone_store_app` directory:
        ```bash
        cd phone_store_app
        ```
4.  **Install Dependencies:** Run the following command in the Terminal (ensure your virtual environment is active if you created one):
    ```bash
    pip install PyQt6 fpdf2
    ```
    *Note: If you previously encountered issues with `fpdf2` and the `Incorrect unit: mm` error, using a clean virtual environment as described in step 3 is the recommended way to avoid conflicts.* 

## Running the Application

1.  **Navigate to Directory:** Make sure your Terminal is in the `phone_store_app` directory and your virtual environment (if created) is active.
2.  **Run the Script:** Execute the main application file using Python 3:
    ```bash
    python main.py
    ```
3.  The application window should appear.

## Usage

*   **Language:** Use the "Language" menu to switch between English, French, and Arabic.
*   **Inventory Tab:** 
    *   View current stock.
    *   Use the buttons at the bottom to Add, Edit, or Delete products.
*   **Sales Tab:**
    *   Select a product from the dropdown list.
    *   Choose the quantity.
    *   Click "Add to Cart".
    *   The cart table on the right will update.
    *   Once all items are added, click "Process Sale & Generate Invoice".
    *   The sale will be recorded, inventory updated, and you will be prompted to save the generated PDF invoice.
*   **Reports Tab:** (New!)
    *   **Daily Report:** Select a specific date using the calendar dropdown and click "Generate Report" to see total sales and profit for that day.
    *   **Yearly Report:** Select a year using the number input and click "Generate Report" to see total sales and profit for that entire year.
    *   *Profit is calculated as (Selling Price at time of sale - Original Price at time of sale) * Quantity Sold.* 
*   **Data File:** The `store_data.db` file will be created/updated in the same directory as `main.py`. Do not delete this file unless you want to reset all application data.

## Developer

Developed by Youssef (as requested).


