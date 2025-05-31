# Phone Store Management App - Todo List

This file tracks the development progress of the phone store management application.

**Phase 1: Initial Development & Bug Fixes**

- [x] Analyze user requirements and create a detailed plan.
- [x] Choose and set up the Python GUI library (PyQt6).
- [x] Design the overall application layout, navigation structure.
- [x] Implement the multilingual framework using JSON files.
  - [x] Populate English translations (`en.json`).
  - [x] Populate French translations (`fr.json`).
  - [x] Populate Arabic translations (`ar.json`).
- [x] Implement the Inventory Management module:
  - [x] Set up a database (SQLite) for offline data storage.
  - [x] Create UI for adding new phone models.
  - [x] Create UI for viewing/listing current stock.
  - [x] Create UI for updating phone details and stock levels.
- [x] Implement the Sales and Invoicing module:
  - [x] Create UI for processing sales.
  - [x] Implement invoice data generation.
  - [x] Implement PDF invoice generation (using FPDF2, ensuring Arabic support).
  - [x] Implement functionality to view past invoices (DB structure ready, UI deferred).
  - [x] Clarify and implement invoice 'editing' functionality (PDF generated post-sale).
- [x] Implement the real-time clock display in the UI.
- [x] Add the requested footer.
- [x] Ensure the application runs offline.
- [x] Test all features thoroughly.
- [x] Prepare the application files and provide instructions for running on macOS M1.
- [x] Fix `AttributeError: module 'database' has no attribute 'get_product_by_id'` bug.
- [x] Fix PDF generation bug (`FPDF error: Incorrect unit: mm` - resolved via environment setup).
- [x] Fix product deletion bug (Verified working after review).

**Phase 2: Reporting Features**

- [x] Analyze new reporting requirements (Daily/Yearly Sales & Profit).
- [x] Update database schema and logic to store original cost at time of sale for accurate profit calculation.
- [x] Design and implement UI for displaying reports (e.g., a new 'Reports' tab).
- [x] Develop functions to calculate daily sales and profit.
- [x] Develop functions to calculate yearly sales and profit.
- [x] Update translation files (`en.json`, `fr.json`, `ar.json`) with new report-related text.
- [x] Test the reporting features thoroughly.
- [ ] Prepare updated application files and documentation.

