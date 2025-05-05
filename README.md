📱 Phone Store Inventory Management System
A Django-based inventory and sales management system designed for phone retail businesses. This platform enables streamlined management of phone and accessory inventories, provides a Point of Sale (POS) interface, and tracks all sales and stock movements. The system features two user roles: Admin and Staff.

🚀 Features
🔐 User Roles
Admin App

Manage inventory and sales

Add/edit/delete phones and accessories

Add and manage staff users

View sales reports and stock levels

Export reports to Excel/PDF

SMS/Email alerts for low stock

Multi-branch store support

Staff App

Use POS to handle customer transactions

View inventory (with limited permissions)

Record sales and track available stock

🛒 Point of Sale (POS)
User-friendly POS interface

Quick product lookup and checkout process

Auto-updates inventory after each sale

📦 Inventory Management
Add, edit, and remove phones and accessories

Track stock levels and product categories

Monitor low-stock alerts

💰 Sales Tracking
Log and filter sales by date, product, or staff

Exportable sales reports

Dashboard summary of daily, weekly, or monthly sales

🧰 Tech Stack
Framework: Django 4.x

Database: SQLite (default), can be switched to PostgreSQL or MySQL

Frontend: HTML, CSS, Bootstrap, JavaScript

Authentication: Django built-in auth with role-based access

🛠️ Installation (Django)

📁 Project Structure

phone-store-inventory/
├── admin/              # Admin app for inventory and sales control
├── staff/              # Staff app for POS and restricted access
├── templates/          # Shared HTML templates
├── static/             # CSS, JS, images
├── db.sqlite3          # Default SQLite database
├── manage.py
├── requirements.txt
└── README.md
👥 User Roles & Permissions
Role	Access Level	Capabilities
Admin	Full	Manage users, inventory, sales, reports
Staff	Limited	POS usage, view products, log sales

🔐 Authentication
Role-based access via Django Groups or Custom User Models

Admin dashboard access secured via Django admin

📊 Future Enhancements
Barcode scanning via external devices


