import streamlit as st
import pandas as pd
import json
import os
import datetime
import time

# ================= CONFIGURATION =================
st.set_page_config(
    page_title="GourmetOS PH",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File for data persistence
DB_FILE = "restaurant_db.json"

# Default Data (Philippines Context)
DEFAULT_DATA = {
    "menu": [
        {"id": 1, "name": "Truffle Burger", "category": "Burger", "price": 295.00, "img": "🍔"},
        {"id": 2, "name": "Ribeye Steak", "category": "Main", "price": 1200.00, "img": "🥩"},
        {"id": 3, "name": "Caesar Salad", "category": "Main", "price": 220.00, "img": "🥗"},
        {"id": 4, "name": "Iced Tea", "category": "Drink", "price": 85.00, "img": "🍹"},
        {"id": 5, "name": "Halo-Halo", "category": "Dessert", "price": 150.00, "img": "🍧"},
        {"id": 6, "name": "Crispy Pata", "category": "Main", "price": 650.00, "img": "🍖"},
        {"id": 7, "name": "San Miguel", "category": "Drink", "price": 90.00, "img": "🍺"},
        {"id": 8, "name": "Sisig", "category": "Main", "price": 250.00, "img": "🍳"}
    ],
    "staff": [
        {"id": 1, "name": "Juan dela Cruz", "role": "Manager", "status": "Active"},
        {"id": 2, "name": "Maria Clara", "role": "Chef", "status": "Active"}
    ],
    "tables": [{"id": i+1, "status": "Free"} for i in range(8)],
    "reservations": [],
    "sales": [],
    "orders": []  # Active kitchen orders
}

# ================= FUNCTIONS =================

def load_data():
    if not os.path.exists(DB_FILE):
        return DEFAULT_DATA
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_DATA

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def format_peso(amount):
    return f"₱{amount:,.2f}"

# Initialize Session State
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'cart' not in st.session_state:
    st.session_state.cart = {} # {item_id: quantity}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'last_order_receipt' not in st.session_state:
    st.session_state.last_order_receipt = None

# ================= AUTHENTICATION =================

def login_screen():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1000&q=80");
            background-size: cover;
        }
        .login-box {
            background-color: rgba(0,0,0,0.8);
            padding: 30px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="login-box"><h2>GourmetOS PH</h2><p>Enterprise Login</p></div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="admin123")
        
        if st.button("Secure Login", type="primary", use_container_width=True):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Credentials")

# ================= APP MODULES =================

def sidebar_nav():
    with st.sidebar:
        st.title("🍽️ GourmetOS")
        st.caption("Philippines Edition")
        
        menu = st.radio(
            "Navigation",
            ["Dashboard", "Point of Sale", "Kitchen Display", "Reservations", "Staff", "Menu Manager", "Tables"],
            index=0
        )
        
        st.divider()
        st.info(f"User: Admin\nStatus: Online 🟢")
        
        if st.button("Logout", icon="🔒"):
            st.session_state.logged_in = False
            st.rerun()
            
    return menu

# --- DASHBOARD ---
def render_dashboard():
    st.title("📊 Manager Dashboard")
    
    data = st.session_state.data
    sales_df = pd.DataFrame(data['sales'])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = sum(s['total'] for s in data['sales'])
    total_orders = len(data['sales'])
    active_staff = len([s for s in data['staff'] if s['status'] == 'Active'])
    reservations = len(data['reservations'])
    
    col1.metric("Total Revenue", format_peso(total_revenue), "+12%")
    col2.metric("Total Orders", total_orders, "+5")
    col3.metric("Reservations", reservations, "Today")
    col4.metric("Active Staff", active_staff)
    
    st.divider()
    
    # Charts & Tables
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Recent Revenue Trend")
        if not sales_df.empty:
            sales_df['time_obj'] = pd.to_datetime(sales_df['time'])
            chart_data = sales_df.groupby('time')['total'].sum()
            st.line_chart(chart_data)
        else:
            st.info("No sales data yet.")

    with c2:
        st.subheader("Top Selling Categories")
        if not sales_df.empty:
            # Flatten items to count categories
            all_items = []
            for s in data['sales']:
                all_items.extend(s['items'])
            
            if all_items:
                cat_df = pd.DataFrame(all_items)
                cat_counts = cat_df['category'].value_counts()
                st.bar_chart(cat_counts)
            else:
                st.caption("No items sold yet")
        else:
            st.caption("No data")

    # Recent Transactions Table
    st.subheader("Recent Transactions")
    if not sales_df.empty:
        display_df = sales_df[['id', 'time', 'total', 'status']].copy()
        display_df['total'] = display_df['total'].apply(lambda x: format_peso(x))
        st.dataframe(display_df.sort_values(by="id", ascending=False), use_container_width=True)
        
        # CSV Export
        csv = sales_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sales Report (CSV)", csv, "sales_report.csv", "text/csv")
    else:
        st.info("No transactions found.")

# --- POS SYSTEM ---
def render_pos():
    st.title("🏪 Point of Sale")
    
    col_menu, col_cart = st.columns([2, 1])
    
    # --- Menu Grid ---
    with col_menu:
        # Category Filter
        categories = ["All"] + sorted(list(set(item['category'] for item in st.session_state.data['menu'])))
        selected_cat = st.pills("Category", categories, default="All")
        
        st.divider()
        
        # Item Grid
        items = st.session_state.data['menu']
        if selected_cat != "All":
            items = [i for i in items if i['category'] == selected_cat]
        
        # Create grid columns
        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"<h1 style='text-align:center'>{item['img']}</h1>", unsafe_allow_html=True)
                    st.markdown(f"**{item['name']}**")
                    st.markdown(f"<span style='color:green; font-weight:bold'>{format_peso(item['price'])}</span>", unsafe_allow_html=True)
                    
                    if st.button("Add", key=f"add_{item['id']}", use_container_width=True):
                        item_id = str(item['id'])
                        if item_id in st.session_state.cart:
                            st.session_state.cart[item_id] += 1
                        else:
                            st.session_state.cart[item_id] = 1
                        st.toast(f"Added {item['name']}", icon="🛒")

    # --- Cart Section ---
    with col_cart:
        st.subheader("🛒 Current Order")
        
        cart_total = 0
        cart_items_list = []
        
        if not st.session_state.cart:
            st.info("Cart is empty")
        else:
            for item_id, qty in list(st.session_state.cart.items()):
                # Find item details
                item = next((i for i in st.session_state.data['menu'] if str(i['id']) == item_id), None)
                if item:
                    item_total = item['price'] * qty
                    cart_total += item_total
                    cart_items_list.append({**item, "qty": qty})
                    
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(f"**{item['name']}**")
                        st.caption(f"{format_peso(item['price'])} x {qty}")
                    with c2:
                        st.write(f"**{format_peso(item_total)}**")
                    with c3:
                        if st.button("❌", key=f"del_{item_id}"):
                            del st.session_state.cart[item_id]
                            st.rerun()
            
            st.divider()
            
            # Totals
            tax = cart_total * 0.12 # 12% VAT context
            final_total = cart_total
            
            c_sub1, c_sub2 = st.columns(2)
            c_sub1.write("Subtotal:")
            c_sub2.write(format_peso(cart_total - tax))
            
            c_tax1, c_tax2 = st.columns(2)
            c_tax1.write("VAT (12%):")
            c_tax2.write(format_peso(tax))
            
            st.markdown(f"### Total: {format_peso(final_total)}")
            
            # Checkout
            if st.button("💰 Checkout & Print", type="primary", use_container_width=True):
                # Process Order
                new_order = {
                    "id": int(time.time()),
                    "items": cart_items_list,
                    "total": final_total,
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Cooking"
                }
                
                # Save to Data
                st.session_state.data['sales'].append(new_order)
                st.session_state.data['orders'].append(new_order) # Active orders
                save_data(st.session_state.data)
                
                # Clear Cart and Set Receipt
                st.session_state.cart = {}
                st.session_state.last_order_receipt = new_order
                st.rerun()

    # --- Receipt Modal (Simulated) ---
    if st.session_state.last_order_receipt:
        order = st.session_state.last_order_receipt
        with st.expander("🧾 Receipt Generated (Click to View)", expanded=True):
            st.markdown("---")
            st.markdown(f"<h3 style='text-align:center'>GOURMET OS PH</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center'>Order #{order['id']}<br>{order['time']}</p>", unsafe_allow_html=True)
            st.markdown("---")
            for i in order['items']:
                st.markdown(f"**{i['qty']}x** {i['name']} - {format_peso(i['price'] * i['qty'])}")
            st.markdown("---")
            st.markdown(f"### TOTAL: {format_peso(order['total'])}")
            st.markdown("---")
            col_print1, col_print2 = st.columns(2)
            if col_print1.button("🖨️ Print"):
                st.toast("Sent to printer...")
            if col_print2.button("Close Receipt"):
                st.session_state.last_order_receipt = None
                st.rerun()

# --- KITCHEN DISPLAY ---
def render_kitchen():
    st.title("🔥 Kitchen Display System")
    
    # Filter active orders
    active_orders = [o for o in st.session_state.data['orders'] if o['status'] == 'Cooking']
    
    if not active_orders:
        st.success("All orders completed! Kitchen is clear.")
    
    # Auto-refresh mechanism simulated
    if st.button("🔄 Refresh Orders"):
        st.rerun()

    cols = st.columns(3)
    for idx, order in enumerate(active_orders):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"#### Order #{str(order['id'])[-4:]}")
                st.caption(f"🕒 {order['time']}")
                st.divider()
                
                for item in order['items']:
                    st.markdown(f"- **{item['qty']}x** {item['name']}")
                
                st.divider()
                if st.button("✅ Mark Ready", key=f"k_{order['id']}", type="primary", use_container_width=True):
                    # Update status
                    order_index = next((i for i, o in enumerate(st.session_state.data['orders']) if o['id'] == order['id']), None)
                    sales_index = next((i for i, o in enumerate(st.session_state.data['sales']) if o['id'] == order['id']), None)
                    
                    if order_index is not None:
                        st.session_state.data['orders'][order_index]['status'] = "Ready"
                        st.session_state.data['orders'].pop(order_index) # Remove from active kitchen view
                    if sales_index is not None:
                        st.session_state.data['sales'][sales_index]['status'] = "Completed"
                        
                    save_data(st.session_state.data)
                    st.rerun()

# --- RESERVATIONS ---
def render_reservations():
    st.title("📅 Reservations")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        with st.form("res_form"):
            st.subheader("New Booking")
            name = st.text_input("Customer Name")
            r_time = st.time_input("Time")
            guests = st.number_input("Guests", min_value=1, value=2)
            if st.form_submit_button("Book Table"):
                new_res = {
                    "id": int(time.time()),
                    "name": name,
                    "time": str(r_time),
                    "guests": guests
                }
                st.session_state.data['reservations'].append(new_res)
                save_data(st.session_state.data)
                st.success("Booked!")
                st.rerun()
                
    with c2:
        st.subheader("Upcoming Bookings")
        if st.session_state.data['reservations']:
            df = pd.DataFrame(st.session_state.data['reservations'])
            
            # Custom display with delete
            for idx, row in df.iterrows():
                with st.container(border=True):
                    col_det, col_act = st.columns([3, 1])
                    with col_det:
                        st.write(f"**{row['name']}** - {row['guests']} Pax")
                        st.caption(f"🕒 {row['time']}")
                    with col_act:
                        if st.button("Cancel", key=f"del_res_{row['id']}"):
                            st.session_state.data['reservations'] = [r for r in st.session_state.data['reservations'] if r['id'] != row['id']]
                            save_data(st.session_state.data)
                            st.rerun()
        else:
            st.info("No reservations.")

# --- STAFF MANAGEMENT ---
def render_staff():
    st.title("👥 Staff Management")
    
    tab1, tab2 = st.tabs(["Staff List", "Add Staff"])
    
    with tab1:
        staff_df = pd.DataFrame(st.session_state.data['staff'])
        if not staff_df.empty:
            st.dataframe(staff_df, use_container_width=True)
            
            # Delete interface
            st.subheader("Manage Staff")
            staff_to_remove = st.selectbox("Select Staff to Remove", options=[s['name'] for s in st.session_state.data['staff']])
            if st.button("Remove Staff", type="secondary"):
                st.session_state.data['staff'] = [s for s in st.session_state.data['staff'] if s['name'] != staff_to_remove]
                save_data(st.session_state.data)
                st.success("Removed.")
                st.rerun()
        else:
            st.info("No staff data.")
            
    with tab2:
        with st.form("add_staff"):
            name = st.text_input("Full Name")
            role = st.selectbox("Role", ["Manager", "Chef", "Waiter", "Cashier"])
            if st.form_submit_button("Hire Staff"):
                new_staff = {
                    "id": int(time.time()),
                    "name": name,
                    "role": role,
                    "status": "Active"
                }
                st.session_state.data['staff'].append(new_staff)
                save_data(st.session_state.data)
                st.success("Staff added!")
                st.rerun()

# --- MENU MANAGER ---
def render_menu():
    st.title("📖 Menu Management")
    
    with st.expander("➕ Add New Item"):
        with st.form("new_item"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Item Name")
            price = col2.number_input("Price (PHP)", min_value=0.0)
            cat = col1.selectbox("Category", ["Main", "Burger", "Drink", "Dessert", "Side"])
            img = col2.selectbox("Icon", ["🍔", "🍕", "🥩", "🥗", "🍹", "☕", "🍰", "🍚", "🍝"])
            
            if st.form_submit_button("Add Item"):
                new_item = {
                    "id": int(time.time()),
                    "name": name,
                    "category": cat,
                    "price": price,
                    "img": img
                }
                st.session_state.data['menu'].append(new_item)
                save_data(st.session_state.data)
                st.success(f"{name} added!")
                st.rerun()
    
    st.divider()
    
    # Edit/Delete Table
    st.subheader("Current Menu")
    
    for item in st.session_state.data['menu']:
        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
        col1.markdown(f"### {item['img']}")
        col2.write(f"**{item['name']}**")
        col3.caption(item['category'])
        col4.write(format_peso(item['price']))
        if col5.button("🗑️", key=f"del_menu_{item['id']}"):
            st.session_state.data['menu'] = [i for i in st.session_state.data['menu'] if i['id'] != item['id']]
            save_data(st.session_state.data)
            st.rerun()
        st.divider()

# --- TABLES ---
def render_tables():
    st.title("🪑 Table Status")
    
    tables = st.session_state.data['tables']
    cols = st.columns(4)
    
    for idx, table in enumerate(tables):
        is_free = table['status'] == "Free"
        color = "green" if is_free else "red"
        status_icon = "🟢 Available" if is_free else "🔴 Occupied"
        
        with cols[idx % 4]:
            with st.container(border=True):
                st.markdown(f"<h3 style='color:{color}'>Table {table['id']}</h3>", unsafe_allow_html=True)
                st.markdown(f"**{status_icon}**")
                
                if st.button("Toggle Status", key=f"tab_{table['id']}"):
                    # Toggle logic
                    new_status = "Occupied" if is_free else "Free"
                    st.session_state.data['tables'][idx]['status'] = new_status
                    save_data(st.session_state.data)
                    st.rerun()

# ================= MAIN EXECUTION =================

if not st.session_state.logged_in:
    login_screen()
else:
    selection = sidebar_nav()
    
    if selection == "Dashboard":
        render_dashboard()
    elif selection == "Point of Sale":
        render_pos()
    elif selection == "Kitchen Display":
        render_kitchen()
    elif selection == "Reservations":
        render_reservations()
    elif selection == "Staff":
        render_staff()
    elif selection == "Menu Manager":
        render_menu()
    elif selection == "Tables":
        render_tables()