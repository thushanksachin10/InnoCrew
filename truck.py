# test_after_fix.py
from database.models import db
from whatsapp.webhook import handle_message

def test_after_fix():
    """Test trip planning after fixing truck statuses"""
    print("🚚 Testing Trip Planning After Fix")
    print("=" * 60)
    
    # Show current truck status
    trucks = db.get_all_trucks()
    print(f"\n📊 Current Truck Status:")
    for truck in trucks:
        status_emoji = "✅" if truck.get('status') == 'available' else "🚚" if truck.get('status') == 'in_transit' else "📋"
        print(f"  {status_emoji} {truck.get('id')}: {truck.get('number')} in {truck.get('location')} ({truck.get('status')})")
    
    print("\n" + "=" * 60)
    
    # Test trip planning
    test_cases = [
        "Mumbai to Delhi",
        "start a trip from Pune to jaipur",
        "from Delhi to Mumbai",
        "Pune to Agra",
        "help",
        "fleet status"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}. 📤 Testing: '{message}'")
        print("-" * 40)
        
        try:
            response = handle_message(message, "+919999999999")
            
            # Check if it's an error
            if "❌" in response or "error" in response.lower():
                print(f"❌ Error response:")
                print(response[:300])
            else:
                print(f"✅ Success! Response length: {len(response)} chars")
                print(f"Preview: {response[:200]}...")
                
                # Show what truck was selected if trip was planned
                if "Trip Planned" in response or "trip planned" in response.lower():
                    # Extract truck info from response
                    import re
                    truck_match = re.search(r"Truck.*?: (.*?)\n", response)
                    if truck_match:
                        print(f"🚛 Selected truck: {truck_match.group(1)}")
                    
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete!")

if __name__ == "__main__":
    test_after_fix()