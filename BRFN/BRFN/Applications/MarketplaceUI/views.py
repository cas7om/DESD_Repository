from django.shortcuts import render

# -------------------------
# Mock data (UI-only)
# -------------------------
CATEGORY_MAP = {
    "vegetables": "Vegetables",
    "dairy": "Dairy",
    "bakery": "Bakery",
    "preserves": "Preserves",
    "seasonal": "Seasonal",
}

MOCK_PRODUCTS = [
    {
        "id": 1,
        "name": "Organic Tomatoes",
        "price": "£2.50",
        "unit": "kg",
        "producer": "Green Farm",
        "badge": "Organic",
        "availability": "Available",
        "category": "vegetables",
        "stock": 25,
        "low_stock_threshold": 10,
        "allergens": [],
        "harvest_date": "2026-02-18",
        "best_before": "2026-03-05",
        "origin": "Somerset, UK",
        "description": "Fresh organic tomatoes, ideal for salads and sauces.",
    },
    {
        "id": 2,
        "name": "Fresh Milk",
        "price": "£1.80",
        "unit": "litre",
        "producer": "Dairy Co",
        "badge": "Local",
        "availability": "Available",
        "category": "dairy",
        "stock": 12,
        "low_stock_threshold": 8,
        "allergens": ["Milk"],
        "harvest_date": "2026-02-22",
        "best_before": "2026-02-28",
        "origin": "Bristol, UK",
        "description": "Local fresh milk from grass-fed cows.",
    },
    {
        "id": 3,
        "name": "Sourdough Bread",
        "price": "£3.20",
        "unit": "per item",
        "producer": "Bristol Bakery",
        "badge": "Artisan",
        "availability": "Available",
        "category": "bakery",
        "stock": 8,
        "low_stock_threshold": 6,
        "allergens": ["Gluten"],
        "harvest_date": "2026-02-23",
        "best_before": "2026-02-26",
        "origin": "Bristol, UK",
        "description": "Handmade sourdough loaf baked fresh daily.",
    },
    {
        "id": 4,
        "name": "Seasonal Strawberries",
        "price": "£4.00",
        "unit": "per punnet",
        "producer": "Red Fields",
        "badge": "In season",
        "availability": "In Season",
        "category": "seasonal",
        "stock": 3,
        "low_stock_threshold": 5,
        "allergens": [],
        "harvest_date": "2026-02-20",
        "best_before": "2026-02-24",
        "origin": "Kent, UK",
        "description": "Sweet seasonal strawberries (limited availability).",
    },
    # İstersen Unavailable örneği ekleyip marketplace’te gizlendiğini gösterebiliriz:
    {
        "id": 5,
        "name": "Out-of-season Asparagus",
        "price": "£5.50",
        "unit": "bundle",
        "producer": "Green Farm",
        "badge": "Seasonal",
        "availability": "Unavailable",
        "category": "vegetables",
        "stock": 0,
        "low_stock_threshold": 5,
        "allergens": [],
        "harvest_date": "—",
        "best_before": "—",
        "origin": "Somerset, UK",
        "description": "Currently unavailable (out of season).",
    },
]

MOCK_ORDERS = [
    {
        "id": 101,
        "status": "Pending",
        "customer": "Alex",
        "customer_phone": "—",
        "customer_email": "—",
        "order_date": "2026-02-23",
        "delivery_date": "2026-02-25",
        "address_line1": "12 Market Street",
        "address_line2": "Flat 2B",
        "postcode": "BS1 4AA",
        "instructions": "Leave at reception if not home.",
        "items": [
            {"name": "Organic Tomatoes", "qty": 2, "unit_price": "£2.50", "line_total": "£5.00"},
            {"name": "Sourdough Bread", "qty": 1, "unit_price": "£3.20", "line_total": "£3.20"},
        ],
        "total": "£8.20",
    },
    {
        "id": 102,
        "status": "Confirmed",
        "customer": "Sam",
        "customer_phone": "—",
        "customer_email": "—",
        "order_date": "2026-02-22",
        "delivery_date": "2026-02-24",
        "address_line1": "7 Riverside Road",
        "address_line2": "",
        "postcode": "BS2 1ZZ",
        "instructions": "Call on arrival.",
        "items": [
            {"name": "Fresh Milk", "qty": 2, "unit_price": "£1.80", "line_total": "£3.60"},
        ],
        "total": "£3.60",
    },
    {
        "id": 103,
        "status": "Ready",
        "customer": "Jamie",
        "customer_phone": "—",
        "customer_email": "—",
        "order_date": "2026-02-21",
        "delivery_date": "2026-02-23",
        "address_line1": "44 Station Lane",
        "address_line2": "",
        "postcode": "BS5 9XY",
        "instructions": "No substitutions please.",
        "items": [
            {"name": "Seasonal Strawberries", "qty": 2, "unit_price": "£4.00", "line_total": "£8.00"},
        ],
        "total": "£8.00",
    },
]


def _find_product(pid: int):
    return next((p for p in MOCK_PRODUCTS if p["id"] == pid), MOCK_PRODUCTS[0])


def _find_order(oid: int):
    return next((o for o in MOCK_ORDERS if o["id"] == oid), MOCK_ORDERS[0])


def _market_visible_products(products):
    # TC-004/005: Unavailable ürünler marketplace’te görünmesin
    return [p for p in products if p.get("availability") != "Unavailable"]


# -------------------------
# Marketplace (customer UI)
# -------------------------
def home(request):
    return render(request, "market/home.html", {"products": _market_visible_products(MOCK_PRODUCTS)})


def category(request, slug):
    slug = (slug or "").lower().strip()
    filtered = [p for p in MOCK_PRODUCTS if p.get("category") == slug]
    return render(
        request,
        "market/category.html",
        {
            "category": CATEGORY_MAP.get(slug, slug),
            "category_slug": slug,
            "products": _market_visible_products(filtered),
        },
    )


def product_detail(request, pid):
    product = _find_product(pid)
    return render(request, "market/product_detail.html", {"product": product})


def search(request):
    q = (request.GET.get("q", "") or "").strip()
    visible = _market_visible_products(MOCK_PRODUCTS)

    if not q:
        results = visible
    else:
        q_low = q.lower()
        results = [
            p
            for p in visible
            if q_low in p.get("name", "").lower()
            or q_low in p.get("producer", "").lower()
            or q_low in p.get("origin", "").lower()
        ]

    return render(request, "market/search.html", {"q": q, "products": results})


# -------------------------
# Producer dashboard (UI)
# -------------------------
def producer_products(request):
    return render(request, "producer/products.html", {"products": MOCK_PRODUCTS})


def producer_product_new(request):
    return render(request, "producer/product_form.html", {"mode": "new", "product": None})


def producer_product_edit(request, pid):
    product = _find_product(pid)
    return render(request, "producer/product_form.html", {"mode": "edit", "product": product})


def producer_orders(request):
    return render(request, "producer/orders.html", {"orders": MOCK_ORDERS})


def producer_order_detail(request, oid):
    order = _find_order(oid)
    return render(request, "producer/order_detail.html", {"order": order})


def producer_order_status(request, oid):
    order = _find_order(oid)
    # UI-only timeline örneği
    timeline = [
        {"status": "Pending", "time": "—", "note": "Order received"},
        {"status": "Confirmed", "time": "—", "note": "Producer confirmed"},
        {"status": "Ready", "time": "—", "note": "Packed and ready"},
        {"status": "Delivered", "time": "—", "note": "Completed"},
    ]
    return render(request, "producer/order_status.html", {"order": order, "timeline": timeline})


def producer_payments(request):
    settlements = [
        {"week": "2026-W08", "gross": "£540.00", "commission": "£27.00", "payout": "£513.00"},
        {"week": "2026-W09", "gross": "£410.00", "commission": "£20.50", "payout": "£389.50"},
    ]
    audit = [
        "2026-02-18 — Settlement created for 2026-W08",
        "2026-02-19 — Commission calculated (5%)",
        "2026-02-20 — Payout processed",
    ]
    return render(request, "producer/payments.html", {"settlements": settlements, "audit": audit})


def producer_alerts(request):
    alerts = [
        {"product": "Fresh Milk", "remaining": "12", "threshold": "8", "level": "Low"},
        {"product": "Seasonal Strawberries", "remaining": "3", "threshold": "5", "level": "Critical"},
    ]
    return render(request, "producer/alerts.html", {"alerts": alerts})


# -------------------------
# Admin dashboard (UI)
# -------------------------
def admin_commission(request):
    report_rows = [
        {"order_id": 101, "order_total": "£8.20", "commission": "£0.41", "producer_payout": "£7.79"},
        {"order_id": 102, "order_total": "£3.60", "commission": "£0.18", "producer_payout": "£3.42"},
        {"order_id": 103, "order_total": "£8.00", "commission": "£0.40", "producer_payout": "£7.60"},
    ]
    summary = {
        "total_order_value": "£19.80",
        "total_commission": "£0.99",
        "total_payout": "£18.81",
        "orders_count": 3,
    }
    # Senin template klasörün: templates/network-admin/commission.html
    return render(request, "network-admin/commission.html", {"rows": report_rows, "summary": summary})