# @orders_router.get("")
# def get_orders(db:):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT
#                 Orders.id,
#                 User.name AS user_name,
#                 Product.name AS product_name,
#                 Orders.amount
#             FROM Orders
#             JOIN User
#                 ON Orders.user_id = User.id
#             JOIN Product
#                 ON Orders.product_id = Product.id
#             ORDER BY Orders.id
#         """)
#         rows = cursor.fetchall()
#         return [dict(row) for row in rows]
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()


# @orders_router.post("", status_code=201)
# def create_order(order: OrderCreate):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()

#         cursor.execute("SELECT id FROM User WHERE id = ?", (order.user_id,))
#         if cursor.fetchone() is None:
#             raise HTTPException(status_code=404, detail="未找到使用者")

#         cursor.execute("SELECT id FROM Product WHERE id = ?", (order.product_id,))
#         if cursor.fetchone() is None:
#             raise HTTPException(status_code=404, detail="未找到商品")

#         cursor.execute(
#             """
#             INSERT INTO Orders (user_id, product_id, amount)
#             VALUES (?, ?, ?)
#             """,
#             (order.user_id, order.product_id, order.amount),
#         )
#         conn.commit()

#         return {
#             "id": cursor.lastrowid,
#             "user_id": order.user_id,
#             "product_id": order.product_id,
#             "amount": order.amount,
#         }
#     except HTTPException:
#         raise
#     except sqlite3.IntegrityError:
#         raise HTTPException(status_code=400, detail="訂單資料不正確")
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()

# ==========================================================================================

# @product_router.get("")
# def get_products():
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM Product")
#         rows = cursor.fetchall()
#         return [dict(row) for row in rows]
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()

# @product_router.get("/{id}")
# def get_product(id: int):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM Product WHERE id = ?", (id,))
#         row = cursor.fetchone()

#         if row is None:
#             raise HTTPException(status_code=404, detail="未找到商品")

#         return dict(row)
    
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()

# @product_router.post("", status_code=201)
# def create_product(product: ProductCreate):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO Product (name, price, stock) VALUES (?, ?, ?)",
#             (product.name, product.price, product.stock),
#         )
#         conn.commit()

#         return {
#             "id": cursor.lastrowid,
#             "name": product.name,
#             "price": product.price,
#             "stock": product.stock,
#         }
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()   

# @product_router.put("/{id}")
# def update_product(id: int, product: ProductUpdate):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute(
#             """
#             UPDATE Product
#             SET name = ?, price = ?, stock = ?
#             WHERE id = ?
#             """,
#             (product.name, product.price, product.stock, id),
#         )

#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="未找到商品")

#         conn.commit()

#         return {
#             "id": id,
#             "name": product.name,
#             "price": product.price,
#             "stock": product.stock,
#         }
    
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()

# def delete_product(id: int):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM Product WHERE id = ?", (id,))

#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="未找到商品")

#         conn.commit()
#         return {"message": "商品刪除成功"}
    
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()

# ==========================================================================================

# @user_router.get("")
# def get_users():
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM User")
#         rows = cursor.fetchall()
#         return [dict(row) for row in rows]
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close()


# @user_router.post("", status_code=201)
# def create_user(user: UserCreate):
#     conn = get_connection()
#     try:
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO User (name, email) VALUES (?, ?)",
#             (user.name, user.email),
#         )
#         conn.commit()

#         return {
#             "id": cursor.lastrowid,
#             "name": user.name,
#             "email": user.email,
#         }
#     except sqlite3.IntegrityError:
#         raise HTTPException(status_code=409, detail="Email 已存在")
#     except sqlite3.Error:
#         raise HTTPException(status_code=500, detail="資料庫錯誤")
#     finally:
#         conn.close() 