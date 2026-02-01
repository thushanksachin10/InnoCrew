# clean_users_json.py
import json
from pathlib import Path

# Load the current file
users_file = Path("data/users.json")
with open(users_file, 'r') as f:
    users = json.load(f)

# Remove duplicates based on phone number
unique_users = []
seen_phones = set()

for user in users:
    phone = user.get('phone')
    if phone and phone not in seen_phones:
        seen_phones.add(phone)
        
        # Standardize structure
        standardized_user = {
            'phone': phone,
            'name': user.get('name', 'Unknown'),
            'role': user.get('role', 'customer'),
            'created_at': user.get('created_at', '2024-01-01'),
            'status': user.get('status', 'active')
        }
        
        # Add role-specific fields
        if user.get('role') == 'business':
            standardized_user.update({
                'company': user.get('company', user.get('business_name', 'Unknown')),
                'location': user.get('location', 'Unknown'),
                'type': user.get('type', user.get('category', 'business'))
            })
        elif user.get('role') == 'driver':
            standardized_user['truck_number'] = user.get('truck_number', 'Unknown')
        elif user.get('role') == 'manager':
            standardized_user['company'] = user.get('company', 'Fast Logistics Pvt Ltd')
        
        unique_users.append(standardized_user)

# Save cleaned file
with open(users_file, 'w') as f:
    json.dump(unique_users, f, indent=2)

print(f"✅ Cleaned {len(users)} entries to {len(unique_users)} unique users")
print("Cleaned users:")
for user in unique_users:
    print(f"  - {user['phone']}: {user['name']} ({user['role']})")