# auto_reset_trucks.py
import json
from pathlib import Path
import time

class TruckResetter:
    def __init__(self):
        self.data_dir = Path("data")
        self.trucks_file = self.data_dir / "trucks.json"
        
    def reset_all_trucks(self):
        """Reset all trucks to available status"""
        if not self.trucks_file.exists():
            print("❌ trucks.json not found")
            return False
        
        with open(self.trucks_file, 'r') as f:
            trucks = json.load(f)
        
        for truck in trucks:
            truck['status'] = 'available'
            truck['current_trip_id'] = None
            # Reset load if needed
            truck['current_load_kg'] = 0
        
        with open(self.trucks_file, 'w') as f:
            json.dump(trucks, f, indent=2)
        
        print(f"✅ Reset {len(trucks)} trucks to 'available' status")
        return True
    
    def monitor_and_reset(self, interval_seconds=5):
        """Monitor and reset trucks periodically"""
        print("🔄 Starting truck reset monitor...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.reset_all_trucks()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n🛑 Stopped monitor")

if __name__ == "__main__":
    resetter = TruckResetter()
    resetter.reset_all_trucks()
    # Uncomment for auto-reset: resetter.monitor_and_reset()