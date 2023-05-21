# flask-restaurant

ERD

```
+---------------+
|     users     |
+---------------+
| id (PK)       |
| username      |
| password      |
| phone         |
+---------------+

+---------------+
|    orders     |
+---------------+
| id (PK)       |
| user_id (FK)  |
| table_id (FK) |
| timestamp     |
+---------------+

+---------------+
|     carts     |
+---------------+
| id (PK)       |
| table_id (FK) |
| item_id (FK)  |
| quantity      |
+---------------+

+---------------+
|  menu_items   |
+---------------+
| id (PK)       |
|categories (FK)|
| name          |
| image         |
| price         |
| description   |
+---------------+

+---------------+
|  categories   |
+---------------+
| id (PK)       |
| name          |
+---------------+
```
