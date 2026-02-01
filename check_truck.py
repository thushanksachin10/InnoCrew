# check_trucks.py
import json
from pathlib import Path

def check_and_fix_trucks():
    """Check truck statuses and fix them if needed"""
    data_dir = Path("data")
    trucks_file = data_dir / "trucks.json"
    
    if not trucks_file.exists():
        print("❌ trucks.json not found")
        return
    
    with open(trucks_file, 'r') as f:
        trucks = json.load(f)
    
    print(f"📊 Found {len(trucks)} trucks:")
    print("=" * 80)
    
    fixed_count = 0
    for truck in trucks:
        truck_id = truck.get('id', 'UNKNOWN')
        current_status = truck.get('status', 'unknown')
        location = truck.get('location', 'Unknown')
        
        print(f"{truck_id}: {truck.get('number')} in {location} - Status: {current_status}")
        
        # If status is not 'available', fix it
        if current_status != 'available':
            old_status = truck['status']
            truck['status'] = 'available'
            truck['current_trip_id'] = None
            fixed_count += 1
            print(f"  🔄 Fixed: {old_status} → available")
        else:
            print(f"  ✅ Already available")
        
        print("-" * 80)
    
    # Save the fixed trucks
    if fixed_count > 0:
        with open(trucks_file, 'w') as f:
            json.dump(trucks, f, indent=2)
        print(f"\n✅ Fixed {fixed_count} trucks to 'available' status")
    else:
        print("\n✅ All trucks are already available")
    
    # Show summary
    print(f"\n📋 Summary:")
    print(f"  🚛 Total trucks: {len(trucks)}")
    print(f"  ✅ Available: {len([t for t in trucks if t.get('status') == 'available'])}")
    print(f"  📋 Assigned: {len([t for t in trucks if t.get('status') == 'assigned'])}")
    print(f"  🚚 In Transit: {len([t for t in trucks if t.get('status') == 'in_transit'])}")

if __name__ == "__main__":
    check_and_fix_trucks()