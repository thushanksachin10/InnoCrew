# database/models.py

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class Database:
    def __init__(self):
        self.trucks_file = DATA_DIR / "trucks.json"
        self.trips_file = DATA_DIR / "trips.json"
        self.users_file = DATA_DIR / "users.json"
        self.loads_file = DATA_DIR / "loads.json"
        
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        if not self.trucks_file.exists():
            self._save_json(self.trucks_file, self._get_default_trucks())
        
        if not self.trips_file.exists():
            self._save_json(self.trips_file, [])
        
        if not self.users_file.exists():
            self._save_json(self.users_file, self._get_default_users())
        
        if not self.loads_file.exists():
            self._save_json(self.loads_file, [])
    
    def _get_default_trucks(self):
        return [
            {
                "id": "TRK001",
                "number": "MH01-AB-2211",
                "type": "20ft Container",
                "capacity_kg": 10000,
                "current_load_kg": 0,
                "mileage_kmpl": 5.6,
                "condition": "Good",
                "location": "Mumbai",
                "status": "available",
                "driver_phone": "+919876543210",
                "driver_name": "Rajesh Kumar"
            },
            {
                "id": "TRK002",
                "number": "MH02-CD-3344",
                "type": "14ft Truck",
                "capacity_kg": 7000,
                "current_load_kg": 0,
                "mileage_kmpl": 6.2,
                "condition": "Excellent",
                "location": "Pune",
                "status": "available",
                "driver_phone": "+919876543211",
                "driver_name": "Suresh Patil"
            },
            {
                "id": "TRK003",
                "number": "DL03-EF-5566",
                "type": "22ft Container",
                "capacity_kg": 12000,
                "current_load_kg": 0,
                "mileage_kmpl": 4.8,
                "condition": "Good",
                "location": "Delhi",
                "status": "available",
                "driver_phone": "+919876543212",
                "driver_name": "Amit Sharma"
            }
        ]
    
    def _get_default_users(self):
        return [
            {
                "phone": "+919999999999",
                "name": "Manager",
                "role": "manager",
                "company": "Fast Logistics Pvt Ltd"
            }
        ]
    
    def _load_json(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _save_json(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Truck operations
    def get_all_trucks(self):
        return self._load_json(self.trucks_file)
    
    def get_available_trucks(self, origin=None):
        trucks = self.get_all_trucks()
        available = [t for t in trucks if t['status'] == 'available']
        
        if origin:
            # Prioritize trucks near origin
            available.sort(key=lambda t: 0 if t['location'].lower() == origin.lower() else 1)
        
        return available
    
    def get_truck_by_id(self, truck_id):
        trucks = self.get_all_trucks()
        for truck in trucks:
            if truck['id'] == truck_id:
                return truck
        return None
    
    def update_truck_status(self, truck_id, status, location=None):
        trucks = self.get_all_trucks()
        for truck in trucks:
            if truck['id'] == truck_id:
                truck['status'] = status
                if location:
                    truck['location'] = location
                break
        self._save_json(self.trucks_file, trucks)
    
    # Trip operations
    def create_trip(self, trip_data):
        trips = self._load_json(self.trips_file)
        trip_data['id'] = f"TRIP{len(trips) + 1:03d}"
        trip_data['created_at'] = datetime.now().isoformat()
        trip_data['status'] = 'pending'
        trips.append(trip_data)
        self._save_json(self.trips_file, trips)
        return trip_data
    
    def get_trip_by_id(self, trip_id):
        trips = self._load_json(self.trips_file)
        for trip in trips:
            if trip['id'] == trip_id:
                return trip
        return None
    
    def update_trip_status(self, trip_id, status, location=None):
        trips = self._load_json(self.trips_file)
        for trip in trips:
            if trip['id'] == trip_id:
                trip['status'] = status
                if location:
                    trip['current_location'] = location
                    trip['last_updated'] = datetime.now().isoformat()
                break
        self._save_json(self.trips_file, trips)
    
    def get_active_trips(self):
        trips = self._load_json(self.trips_file)
        return [t for t in trips if t['status'] in ['pending', 'accepted', 'in_progress']]
    
    # Load operations
    def create_load_request(self, load_data):
        loads = self._load_json(self.loads_file)
        load_data['id'] = f"LOAD{len(loads) + 1:03d}"
        load_data['created_at'] = datetime.now().isoformat()
        load_data['status'] = 'pending'
        loads.append(load_data)
        self._save_json(self.loads_file, loads)
        return load_data
    
    def get_pending_loads(self):
        loads = self._load_json(self.loads_file)
        return [l for l in loads if l['status'] == 'pending']
    
    def update_load_status(self, load_id, status, trip_id=None):
        loads = self._load_json(self.loads_file)
        for load in loads:
            if load['id'] == load_id:
                load['status'] = status
                if trip_id:
                    load['trip_id'] = trip_id
                break
        self._save_json(self.loads_file, loads)

# Global database instance
db = Database()
