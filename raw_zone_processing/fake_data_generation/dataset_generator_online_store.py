import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import calendar
import argparse

# Initialize Faker
fake = Faker()

# Product and category definitions with prices and return rates
product_names_by_category = {
    "Clothing": [("T-shirt", 20), ("Jeans", 50), ("Dress", 85), ("Jacket", 120), ("Sweater", 60)],
    "Accessories": [("Belt", 25), ("Bag", 70), ("Watch", 200), ("Hat", 30), ("Scarf", 35)],
    "Footwear": [("Sneakers", 90), ("Shoes", 80), ("Boots", 150), ("Sandals", 50), ("Slippers", 40)],
    "Electronics": [("Phone", 600), ("Laptop", 1000), ("Tablet", 500), ("Smartwatch", 350), ("Headphones", 150)],
    "Jewelry": [("Ring", 250), ("Necklace", 400), ("Earrings", 300), ("Bracelet", 180), ("Pendant", 90)]
}

# Marketing campaigns associated with categories
marketing_campaigns = {
    "Clothing": "Seasonal Sale",
    "Accessories": "New Arrivals",
    "Footwear": "Clearance Sale",
    "Electronics": "Tech Fest",
    "Jewelry": "Exclusive Offer"
}

def generate_custom_ip():
    first_octet = random.choice([8, 9, 10])
    second_octet = random.randint(0, 255)
    third_octet = random.randint(0, 255)
    fourth_octet = random.randint(0, 255)
    return f"{first_octet}.{second_octet}.{third_octet}.{fourth_octet}"

def generate_clients(num_clients):
    european_countries = ['GB', 'ES'] * 20 + ['DE'] * 10 + ['FR', 'DE', 'IT', 'NL', 'PL', 'SE', 'FI', 'NO', 'DK', 'IE', 'PT', 'CZ', 'RO', 'HU', 'SK', 'BG', 'LT', 'LV', 'EE', 'GR', 'HR', 'SI', 'MT', 'CY', 'LU']
    return pd.DataFrame([{
        "client_id": fake.unique.random_int(min=100000, max=999999),
        "country": random.choice(european_countries),
        "customer_type": random.choice(["New", "Returning", "VIP"])
    } for _ in range(num_clients)])

def generate_items_with_categories(num_items):
    items = []
    for _ in range(num_items):
        category = random.choice(list(product_names_by_category.keys()))
        item_name, base_price = random.choice(product_names_by_category[category])
        return_rate = random.uniform(0.01, 0.05)
        items.append({
            "item_id": fake.unique.uuid4(),
            "item_name": item_name,
            "category": category,
            "base_price": round(base_price * random.uniform(0.8, 1.2), 2),
            "marketing_campaign": marketing_campaigns[category],
            "returned": return_rate
        })
    return pd.DataFrame(items)

def generate_browsing_logs(clients, items, num_logs):
    logs = []
    clients_list = clients.to_dict('records')
    items_list = items.to_dict('records')
    for _ in range(num_logs):
        client = random.choice(clients_list)
        item = random.choice(items_list)
        view_date = fake.date_time_this_year(before_now=True, after_now=False)

        if view_date.hour < 8 or view_date.hour > 20:
            if random.random() < 0.2: 
                continue
        if view_date.weekday() >= 5 and random.random() < 0.7: 
            pass

        logs.append({
            "ip": generate_custom_ip(),
            "ts": view_date.strftime('%Y-%m-%d %H:%M:%S'),
            "tz": "UTC",
            "verb": "GET",
            "resource_type": "Item",
            "resource_fk": item['item_id'],
            "response": 200,
            "browser": random.choice(['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']),
            "os": random.choice(['Windows', 'MacOS', 'Linux', 'iOS', 'Android']),
            "customer": client['client_id'],
            "d_day_name": calendar.day_name[view_date.weekday()],
            "i_current_price": item['base_price'],
            "i_category": item['category'],
            "i_description": item['item_name'],
            "c_preferred_cust_flag": random.choice([True, False]),
            "ds": view_date.strftime('%Y-%m-%d')
        })
    return pd.DataFrame(logs)

def generate_transactions(clients, items, browsing_logs):
    """ Generates transactions ensuring no negative time between browse and purchase. """
    transactions = []
    clients_dict = clients.set_index('client_id').to_dict('index')
    items_dict = items.set_index('item_id').to_dict('index')
    for index, row in browsing_logs.iterrows():
        item_details = items_dict[row['resource_fk']]
        campaign = item_details['marketing_campaign'] if random.random() < 0.1 else None 
        client_details = clients_dict[row['customer']]
        browse_time = datetime.strptime(row['ts'], '%Y-%m-%d %H:%M:%S')
        transaction_time = browse_time + timedelta(hours=random.randint(1, 24))  
        is_returned = random.random() < item_details['returned']
        total_amount = round(row['i_current_price'] * random.randint(1, 5), 2)

        transactions.append({
            "client_id": row['customer'],
            "transaction_id": fake.uuid4(),
            "item_id": row['resource_fk'],
            "transaction_date": transaction_time.strftime('%Y-%m-%d %H:%M:%S'),
            "country": client_details['country'],
            "customer_type": client_details['customer_type'],
            "item_description": row['i_description'],
            "category": row['i_category'],
            "quantity": random.randint(1, 5),
            "total_amount": total_amount,
            "marketing_campaign": campaign,
            "returned": is_returned
        })
    return pd.DataFrame(transactions)

def main():
    parser = argparse.ArgumentParser(description='Generate retail datasets with realistic trends.')
    parser.add_argument('num_clients', type=int, help='Number of clients to generate')
    parser.add_argument('num_items', type=int, help='Number of items to generate')
    parser.add_argument('num_transactions', type=int, help='Number of transactions to generate')
    parser.add_argument('num_logs', type=int, help='Number of browsing logs to generate')
    args = parser.parse_args()

    clients = generate_clients(args.num_clients)
    items = generate_items_with_categories(args.num_items)
    browsing_logs = generate_browsing_logs(clients, items, args.num_logs)
    transaction_data = generate_transactions(clients, items, browsing_logs)

    # Save data to CSV
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    browsing_file = f'browsing_data_{timestamp}.csv'
    transaction_file = f'transaction_data_{timestamp}.csv'
    browsing_logs.to_csv(browsing_file, index=False)
    transaction_data.to_csv(transaction_file, index=False)
    print(f'Data generated and saved to CSV files: {browsing_file} and {transaction_file}')

if __name__ == "__main__":
    main()

