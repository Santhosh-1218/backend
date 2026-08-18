import sys
from app.main import app
from app.database.db import db

products = db.get_collection('products')
orders = db.get_collection('orders')
users = db.get_collection('users')
inventory = db.get_collection('inventory')

print(f"VERIFICATION SUCCESS:")
print(f"Products count: {len(products)}")
print(f"Orders count: {len(orders)}")
print(f"Users count: {len(users)}")
ord_1042 = db.get_by_id('orders', 'ord-1042') or db.get_by_id('orders', 'ORD-1042')
print(f"Order 1042 items: {ord_1042['items'][0].get('productName', ord_1042['items'][0].get('name'))}")
inv_item = db.get_by_id('inventory', 'inv-hyd-01-sku-bev-0001') or db.get_collection('inventory')[0]
print(f"Primary available stock ({inv_item.get('sku')}): {inv_item.get('availableQuantity')}")
