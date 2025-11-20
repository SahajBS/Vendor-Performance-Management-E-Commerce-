# =====================================================
# 🚀 Vendor Performance Management System (Final Streamlit Version)
# =====================================================

import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error

# =====================================================
# 🔗 DATABASE CONNECTION
# =====================================================
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",                # ⚠️ change this
        password="home3120",   # ⚠️ change this
        database="vendor_performance_db"
    )

def run_query_df(query, params=None):
    conn = create_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def run_exec(query, params=None):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    conn.close()

# =====================================================
# 🧠 AUTHENTICATION FUNCTIONS
# =====================================================
def login_admin(username, password):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Admin WHERE Username=%s AND Password=%s", (username, password))
    data = cur.fetchone()
    conn.close()
    return data

def login_vendor(email, password):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT Vendor_ID, Name FROM Vendor WHERE Email=%s AND Password=%s", (email, password))
    data = cur.fetchone()
    conn.close()
    return data

def login_customer(email, password):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT Customer_ID, Name FROM Customer WHERE Email=%s AND Password=%s", (email, password))
    data = cur.fetchone()
    conn.close()
    return data

# =====================================================
# 👑 ADMIN DASHBOARD
# =====================================================
def admin_dashboard():
    st.title("👑 Admin Dashboard")

    tabs = st.tabs(["Vendors", "Products", "Orders", "Payments", "Reviews", "Vendor Performance", "Audit Log", "Sales Report"])

    with tabs[0]:
        st.subheader("Vendor Records")
        df = run_query_df("SELECT * FROM Vendor")
        st.dataframe(df, use_container_width=True)

    with tabs[1]:
        df = run_query_df("SELECT * FROM Product")
        st.dataframe(df, use_container_width=True)

    with tabs[2]:
        df = run_query_df("""
            SELECT O.Order_ID, C.Name AS Customer, P.Name AS Product, O.Quantity, O.Status, O.Order_Date
            FROM Orders O
            JOIN Customer C ON O.Customer_ID = C.Customer_ID
            JOIN Product P ON O.Product_ID = P.Product_ID
        """)
        st.dataframe(df, use_container_width=True)

    with tabs[3]:
        df = run_query_df("SELECT * FROM Payment")
        st.dataframe(df, use_container_width=True)

    with tabs[4]:
        df = run_query_df("""
            SELECT R.Review_ID, C.Name AS Customer, V.Name AS Vendor, P.Name AS Product,
                   R.Rating, R.Sentiment, R.Comment, R.Review_Date
            FROM Review R
            JOIN Customer C ON R.Customer_ID = C.Customer_ID
            JOIN Vendor V ON R.Vendor_ID = V.Vendor_ID
            JOIN Product P ON R.Product_ID = P.Product_ID
        """)
        st.dataframe(df, use_container_width=True)

    with tabs[5]:
        df = run_query_df("""
            SELECT Vendor_ID, Avg_Review_Rating, Last_Feedback_Date
            FROM Vendor_Performance
            ORDER BY Avg_Review_Rating DESC
        """)
        st.dataframe(df, use_container_width=True)

    with tabs[6]:
        df = run_query_df("SELECT Log_ID, Table_Name, Operation, Record_ID, Operation_Time FROM Audit_Log ORDER BY Operation_Time DESC")
        st.dataframe(df, use_container_width=True)

    with tabs[7]:
        st.subheader("📊 Vendor Sales Report")
        df = run_query_df("""
            SELECT 
                v.Vendor_ID,
                v.Name,
                v.Business_Type,
                v.Avg_Review_Rating,
                IFNULL(SUM(p.Amount), 0) AS Total_Sales
            FROM Vendor v
            LEFT JOIN Product pr ON v.Vendor_ID = pr.Vendor_ID
            LEFT JOIN Orders o ON pr.Product_ID = o.Product_ID
            LEFT JOIN Payment p ON o.Order_ID = p.Order_ID AND p.Payment_Status = 'Completed'
            GROUP BY v.Vendor_ID, v.Name, v.Business_Type, v.Avg_Review_Rating
            ORDER BY Total_Sales DESC
        """)
        st.dataframe(df, use_container_width=True)

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# =====================================================
# 🧑‍💼 VENDOR DASHBOARD (With Delivery Status Fix)
# =====================================================
def vendor_dashboard(vendor_id, vendor_name):
    st.title(f"🧑‍💼 Vendor Dashboard — {vendor_name}")
    tabs = st.tabs(["My Products", "Orders", "Reviews", "Performance", "Sales Summary", "Add Product"])

    # PRODUCTS TAB
    with tabs[0]:
        st.subheader("📦 My Products")
        df = run_query_df("SELECT * FROM Product WHERE Vendor_ID=%s", (vendor_id,))
        st.dataframe(df, use_container_width=True)

    # ORDERS TAB
    with tabs[1]:
        st.subheader("📜 Orders and Delivery Status")
        df = run_query_df("""
            SELECT 
                O.Order_ID, 
                C.Name AS Customer, 
                P.Name AS Product, 
                O.Quantity, 
                O.Status, 
                O.Order_Date
            FROM Orders O
            JOIN Customer C ON O.Customer_ID = C.Customer_ID
            JOIN Product P ON O.Product_ID = P.Product_ID
            WHERE P.Vendor_ID=%s
            ORDER BY O.Order_Date DESC;
        """, (vendor_id,))
        if df.empty:
            st.info("No orders found yet.")
        else:
            st.dataframe(df, use_container_width=True)

            st.markdown("---")
            st.subheader("🚚 Update Delivery Status")
            order_id = st.number_input("Enter Order ID to update:", min_value=1, step=1)
            new_status = st.selectbox("Select New Status", ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"])

            if st.button("Update Order Status"):
                try:
                    verify = run_query_df("""
                        SELECT COUNT(*) AS cnt
                        FROM Orders O
                        JOIN Product P ON O.Product_ID = P.Product_ID
                        WHERE O.Order_ID=%s AND P.Vendor_ID=%s
                    """, (order_id, vendor_id))

                    if verify.iloc[0]['cnt'] == 0:
                        st.error("❌ This order does not belong to you.")
                    else:
                        run_exec("UPDATE Orders SET Status=%s WHERE Order_ID=%s", (new_status, order_id))
                        st.success(f"✅ Order #{order_id} status updated to '{new_status}'")
                        st.rerun()
                except Error as e:
                    st.error(f"Database error: {e}")

    # REVIEWS TAB
    with tabs[2]:
        st.subheader("💬 Reviews Received")
        df = run_query_df("""
            SELECT R.Review_ID, C.Name AS Customer, R.Rating, R.Sentiment, R.Comment, R.Review_Date
            FROM Review R
            JOIN Customer C ON R.Customer_ID = C.Customer_ID
            WHERE R.Vendor_ID=%s
            ORDER BY R.Review_Date DESC
        """, (vendor_id,))
        st.dataframe(df, use_container_width=True)

    # PERFORMANCE TAB
    with tabs[3]:
        st.subheader("📈 Vendor Performance Metrics")
        df = run_query_df("""
            SELECT Vendor_ID, Avg_Review_Rating, Last_Feedback_Date
            FROM Vendor
            WHERE Vendor_ID=%s
        """, (vendor_id,))
        st.dataframe(df, use_container_width=True)

    # SALES SUMMARY TAB
    with tabs[4]:
        st.subheader("💰 Sales Summary")
        
        # Total Sales
        df_total = run_query_df("""
            SELECT IFNULL(SUM(p.Amount), 0) AS Total_Sales
            FROM Payment p
            JOIN Orders o ON p.Order_ID = o.Order_ID
            JOIN Product pr ON o.Product_ID = pr.Product_ID
            WHERE pr.Vendor_ID = %s AND p.Payment_Status = 'Completed'
        """, (vendor_id,))
        
        total_sales = df_total.iloc[0]['Total_Sales']
        st.metric("💵 Total Sales Revenue", f"₹{total_sales:,.2f}")
        
        st.markdown("---")
        
        # Product-wise Sales
        st.subheader("📊 Product-wise Sales Breakdown")
        df_product_sales = run_query_df("""
            SELECT 
                pr.Name AS Product,
                COUNT(o.Order_ID) AS Orders_Count,
                SUM(o.Quantity) AS Units_Sold,
                IFNULL(SUM(p.Amount), 0) AS Revenue
            FROM Product pr
            LEFT JOIN Orders o ON pr.Product_ID = o.Product_ID
            LEFT JOIN Payment p ON o.Order_ID = p.Order_ID AND p.Payment_Status = 'Completed'
            WHERE pr.Vendor_ID = %s
            GROUP BY pr.Product_ID, pr.Name
            ORDER BY Revenue DESC
        """, (vendor_id,))
        
        if df_product_sales.empty:
            st.info("No sales data available yet.")
        else:
            st.dataframe(df_product_sales, use_container_width=True)

    # ADD PRODUCT TAB
    with tabs[5]:
        st.subheader("➕ Add Product")
        name = st.text_input("Product Name")
        desc = st.text_area("Description")
        price = st.number_input("Price (₹)", min_value=0.0, step=0.1)
        stock = st.number_input("Stock Quantity", min_value=0, step=1)
        category = st.selectbox("Category", ["Electronics", "Clothing", "Grocery", "Books", "Home", "Others"])

        if st.button("Add Product"):
            try:
                run_exec("""
                    INSERT INTO Product (Name, Description, Price, Stock, Category, Vendor_ID)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (name, desc, price, stock, category, vendor_id))
                st.success("✅ Product Added Successfully!")
                st.rerun()
            except Error as e:
                st.error(f"Database Error: {e}")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# =====================================================
# 🛒 CUSTOMER DASHBOARD
# =====================================================
def customer_dashboard(customer_id, customer_name):
    st.title(f"🛒 Welcome, {customer_name}")
    tabs = st.tabs(["Browse Products", "My Orders", "Write Review", "Vendor Leaderboard"])

    # Browse Products
    with tabs[0]:
        search = st.text_input("Search Product or Category")
        if search:
            df = run_query_df("""
                SELECT P.Product_ID, P.Name, P.Description, P.Price, P.Stock, P.Category,
                       V.Name AS Vendor, V.Avg_Review_Rating AS Vendor_Rating
                FROM Product P
                JOIN Vendor V ON P.Vendor_ID = V.Vendor_ID
                WHERE P.Name LIKE %s OR P.Category LIKE %s
            """, (f"%{search}%", f"%{search}%"))
        else:
            df = run_query_df("""
                SELECT P.Product_ID, P.Name, P.Description, P.Price, P.Stock, P.Category,
                       V.Name AS Vendor, V.Avg_Review_Rating AS Vendor_Rating
                FROM Product P
                JOIN Vendor V ON P.Vendor_ID = V.Vendor_ID
                ORDER BY V.Avg_Review_Rating DESC
            """)
        st.dataframe(df, use_container_width=True)

        pid = st.number_input("Product ID", min_value=1, step=1)
        qty = st.number_input("Quantity", min_value=1, step=1)
        pay = st.selectbox("Payment Method", ["UPI", "Credit Card", "Debit Card", "Cash", "Wallet"])

        if st.button("🛍️ Place Order"):
            conn = create_connection()
            cur = conn.cursor()
            cur.execute("SELECT Price, Stock FROM Product WHERE Product_ID=%s", (pid,))
            data = cur.fetchone()
            if not data:
                st.error("Invalid Product ID!")
            else:
                price, stock = data
                if qty > stock:
                    st.error("Insufficient stock ❌")
                else:
                    cur.execute("INSERT INTO Orders (Customer_ID, Product_ID, Quantity, Status) VALUES (%s,%s,%s,'Pending')",
                                (customer_id, pid, qty))
                    order_id = cur.lastrowid
                    amount = price * qty
                    cur.execute("""
                        INSERT INTO Payment (Order_ID, Customer_ID, Payment_Method, Payment_Status, Amount)
                        VALUES (%s,%s,%s,'Completed',%s)
                    """, (order_id, customer_id, pay, amount))
                    conn.commit()
                    st.success(f"✅ Order #{order_id} placed successfully for ₹{amount}")
            conn.close()

    # My Orders
    with tabs[1]:
        st.subheader("📦 My Orders")
        df = run_query_df("""
            SELECT O.Order_ID, P.Name AS Product, O.Quantity, O.Status, O.Order_Date
            FROM Orders O
            JOIN Product P ON O.Product_ID = P.Product_ID
            WHERE O.Customer_ID=%s
            ORDER BY O.Order_Date DESC
        """, (customer_id,))
        st.dataframe(df, use_container_width=True)

    # Write Review
    with tabs[2]:
        st.subheader("⭐ Write a Review")
        df_orders = run_query_df("""
            SELECT DISTINCT O.Product_ID, P.Name
            FROM Orders O
            JOIN Product P ON O.Product_ID = P.Product_ID
            WHERE O.Customer_ID=%s AND O.Status='Delivered'
        """, (customer_id,))
        if df_orders.empty:
            st.info("You can only review delivered products.")
        else:
            product_id = st.selectbox("Select Product", df_orders["Product_ID"],
                                      format_func=lambda x: df_orders.loc[df_orders["Product_ID"]==x, "Name"].values[0])
            rating = st.slider("Rating", 1, 5, 5)
            sentiment = st.selectbox("Sentiment", ["Positive", "Neutral", "Negative"])
            comment = st.text_area("Comment")

            if st.button("Submit Review"):
                conn = create_connection()
                cur = conn.cursor()
                cur.execute("SELECT Vendor_ID FROM Product WHERE Product_ID=%s", (product_id,))
                vendor_id = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM Review WHERE Customer_ID=%s AND Product_ID=%s",
                            (customer_id, product_id))
                if cur.fetchone()[0] > 0:
                    st.warning("❌ You have already reviewed this product!")
                else:
                    cur.execute("""
                        INSERT INTO Review (Customer_ID, Vendor_ID, Product_ID, Comment, Rating, Sentiment)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (customer_id, vendor_id, product_id, comment, rating, sentiment))
                    conn.commit()

                    # call stored procedure
                    cur.callproc('sp_evaluate_vendor', [vendor_id])
                    conn.commit()
                    st.success("✅ Review Submitted Successfully!")
                conn.close()

    # Leaderboard
    with tabs[3]:
        st.subheader("🏆 Vendor Leaderboard")
        df = run_query_df("""
            SELECT 
                v.Vendor_ID,
                v.Name,
                v.Business_Type,
                v.Avg_Review_Rating,
                IFNULL(SUM(p.Amount), 0) AS Total_Sales
            FROM Vendor v
            LEFT JOIN Product pr ON v.Vendor_ID = pr.Vendor_ID
            LEFT JOIN Orders o ON pr.Product_ID = o.Product_ID
            LEFT JOIN Payment p ON o.Order_ID = p.Order_ID AND p.Payment_Status = 'Completed'
            GROUP BY v.Vendor_ID, v.Name, v.Business_Type, v.Avg_Review_Rating
            ORDER BY v.Avg_Review_Rating DESC, Total_Sales DESC
        """)
        st.dataframe(df, use_container_width=True)

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# =====================================================
# 🏁 MAIN FUNCTION
# =====================================================
def main():
    st.set_page_config(page_title="Vendor Performance Portal", layout="wide")
    st.title("🚀 Vendor Performance Management System")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        role = st.session_state.role
        if role == "Admin":
            admin_dashboard()
        elif role == "Vendor":
            vendor_dashboard(st.session_state.user_id, st.session_state.username)
        else:
            customer_dashboard(st.session_state.user_id, st.session_state.username)
        return

    st.sidebar.header("Login / Signup")
    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Select Action", menu)

    if choice == "Login":
        role = st.selectbox("Login As", ["Admin", "Vendor", "Customer"])
        user = st.text_input("Email / Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            if role == "Admin":
                data = login_admin(user, pwd)
                if data:
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Invalid Admin credentials ❌")

            elif role == "Vendor":
                data = login_vendor(user, pwd)
                if data:
                    st.session_state.logged_in = True
                    st.session_state.role = "Vendor"
                    st.session_state.user_id = data[0]
                    st.session_state.username = data[1]
                    st.rerun()
                else:
                    st.error("Invalid Vendor login ❌")

            else:
                data = login_customer(user, pwd)
                if data:
                    st.session_state.logged_in = True
                    st.session_state.role = "Customer"
                    st.session_state.user_id = data[0]
                    st.session_state.username = data[1]
                    st.rerun()
                else:
                    st.error("Invalid Customer login ❌")

    else:
        role = st.selectbox("Register As", ["Vendor", "Customer"])
        if role == "Vendor":
            name = st.text_input("Vendor Name")
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            contact = st.text_input("Contact No")
            business = st.selectbox("Business Type", ["Electronics", "Clothing", "Grocery", "Books", "Home", "Others"])

            if st.button("Register"):
                run_exec("""
                    INSERT INTO Vendor (Name, Email, Password, Contact_No, Business_Type)
                    VALUES (%s,%s,%s,%s,%s)
                """, (name, email, pwd, contact, business))
                st.success("✅ Vendor Registered Successfully!")

        else:
            name = st.text_input("Customer Name")
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            phone = st.text_input("Phone")
            addr = st.text_input("Address")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

            if st.button("Register"):
                run_exec("""
                    INSERT INTO Customer (Name, Email, Password, Phone, Address, Gender)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (name, email, pwd, phone, addr, gender))
                st.success("✅ Customer Registered Successfully!")

if __name__ == "__main__":
    main()
