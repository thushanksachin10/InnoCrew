# database/models.py

import json
from datetime import datetime
from pathlib import Path
from logging_config import get_logger

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class Database:
    def __init__(self):
        self.trucks_file = DATA_DIR / "trucks.json"
        self.trips_file = DATA_DIR / "trips.json"
        self.users_file = DATA_DIR / "users.json"
        self.loads_file = DATA_DIR / "loads.json"
        
        self._init_files()
        logger.info("Database initialized successfully")
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        logger.debug("Checking/initializing data files...")
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
                "max_load_kg": 10000,
                "mileage_kmpl": 5.6,
                "condition": "Good",
                "location": "Mumbai",
                "status": "available",
                "driver_phone": "+919876543210",
                "driver_name": "Rajesh Kumar",
                "fuel_percent": 85,
                "last_maintenance": "2024-01-15",
                "current_trip_id": None,
                "total_distance_km": 125000,
                "next_maintenance_km": 5000,
                "insurance_valid_until": "2024-12-31",
                "permit_valid_until": "2024-12-31",
                "average_speed_kmph": 55,
                "fuel_type": "diesel",
                "owner": "Fast Logistics Pvt Ltd",
                "purchase_date": "2022-05-10",
                "year_of_manufacture": 2021,
                "registration_state": "MH",
                "current_waypoint": None,
                "last_location_update": "2024-01-31T10:00:00",
                "is_gps_enabled": True,
                "emergency_contact": "+919999999999"
            },
            {
                "id": "TRK002",
                "number": "MH02-CD-3344",
                "type": "14ft Truck",
                "capacity_kg": 7000,
                "current_load_kg": 0,
                "max_load_kg": 7000,
                "mileage_kmpl": 6.2,
                "condition": "Excellent",
                "location": "Pune",
                "status": "available",
                "driver_phone": "+919876543211",
                "driver_name": "Suresh Patil",
                "fuel_percent": 90,
                "last_maintenance": "2024-01-10",
                "current_trip_id": None,
                "total_distance_km": 80000,
                "next_maintenance_km": 8000,
                "insurance_valid_until": "2024-11-30",
                "permit_valid_until": "2024-11-30",
                "average_speed_kmph": 60,
                "fuel_type": "diesel",
                "owner": "Fast Logistics Pvt Ltd",
                "purchase_date": "2023-02-15",
                "year_of_manufacture": 2022,
                "registration_state": "MH",
                "current_waypoint": None,
                "last_location_update": "2024-01-31T11:30:00",
                "is_gps_enabled": True,
                "emergency_contact": "+919999999999"
            },
            {
                "id": "TRK003",
                "number": "DL03-EF-5566",
                "type": "22ft Container",
                "capacity_kg": 12000,
                "current_load_kg": 0,
                "max_load_kg": 12000,
                "mileage_kmpl": 4.8,
                "condition": "Good",
                "location": "Delhi",
                "status": "available",
                "driver_phone": "+919876543212",
                "driver_name": "Amit Sharma",
                "fuel_percent": 75,
                "last_maintenance": "2024-01-05",
                "current_trip_id": None,
                "total_distance_km": 150000,
                "next_maintenance_km": 3000,
                "insurance_valid_until": "2024-10-31",
                "permit_valid_until": "2024-10-31",
                "average_speed_kmph": 50,
                "fuel_type": "diesel",
                "owner": "Fast Logistics Pvt Ltd",
                "purchase_date": "2021-08-20",
                "year_of_manufacture": 2020,
                "registration_state": "DL",
                "current_waypoint": None,
                "last_location_update": "2024-01-31T09:45:00",
                "is_gps_enabled": True,
                "emergency_contact": "+919999999999"
            },
            {
                "id": "TRK004",
                "number": "KA04-GH-7788",
                "type": "18ft Truck",
                "capacity_kg": 9000,
                "current_load_kg": 0,
                "max_load_kg": 9000,
                "mileage_kmpl": 5.8,
                "condition": "Excellent",
                "location": "Bangalore",
                "status": "available",
                "driver_phone": "+919876543213",
                "driver_name": "Ramesh Iyer",
                "fuel_percent": 80,
                "last_maintenance": "2024-01-20",
                "current_trip_id": None,
                "total_distance_km": 95000,
                "next_maintenance_km": 6000,
                "insurance_valid_until": "2024-09-30",
                "permit_valid_until": "2024-09-30",
                "average_speed_kmph": 58,
                "fuel_type": "diesel",
                "owner": "Fast Logistics Pvt Ltd",
                "purchase_date": "2022-11-05",
                "year_of_manufacture": 2021,
                "registration_state": "KA",
                "current_waypoint": None,
                "last_location_update": "2024-01-31T12:15:00",
                "is_gps_enabled": True,
                "emergency_contact": "+919999999999"
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
        """Load JSON data from file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            return []
    
    def _save_json(self, file_path, data):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")
    
    # ========== TRUCK OPERATIONS ==========
    
    def get_all_trucks(self):
        """Get all trucks from database"""
        return self._load_json(self.trucks_file)
    
    def get_available_trucks(self, origin=None):
        """Get available trucks, optionally filtered by origin"""
        trucks = self.get_all_trucks()
        available = [t for t in trucks if t.get('status') == 'available']
        
        if origin:
            # Prioritize trucks near origin
            available.sort(key=lambda t: 0 if t.get('location', '').lower() == origin.lower() else 1)
        
        return available
    
    def get_truck_by_id(self, truck_id):
        """Get a specific truck by ID"""
        trucks = self.get_all_trucks()
        for truck in trucks:
            if truck.get('id') == truck_id:
                return truck
        return None
    
    def update_truck_status(self, truck_id, status, location=None):
        """Update truck status and optionally location"""
        trucks = self.get_all_trucks()
        updated = False
        
        for truck in trucks:
            if truck.get('id') == truck_id:
                truck['status'] = status
                if location:
                    truck['location'] = location
                    truck['last_location_update'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            self._save_json(self.trucks_file, trucks)
            logger.info(f"Updated truck {truck_id} status to {status}")
        else:
            logger.warning(f"Truck {truck_id} not found for status update")
    
    # ========== TRIP OPERATIONS ==========
    
    def create_trip(self, trip_data):
        """Create a new trip"""
        trips = self._load_json(self.trips_file)
        
        # Generate trip ID
        trip_id = f"TRIP{len(trips) + 1:03d}"
        trip_data['id'] = trip_id
        trip_data['created_at'] = datetime.now().isoformat()
        trip_data['status'] = 'pending'
        
        trips.append(trip_data)
        self._save_json(self.trips_file, trips)
        
        logger.info(f"Created trip {trip_id}: {trip_data.get('origin')} → {trip_data.get('destination')}")
        return trip_data
    
    def get_trip_by_id(self, trip_id):
        """Get a specific trip by ID"""
        trips = self._load_json(self.trips_file)
        for trip in trips:
            if trip.get('id') == trip_id:
                return trip
        return None
    
    def update_trip_status(self, trip_id, status, location=None):
        """Update trip status"""
        trips = self._load_json(self.trips_file)
        updated = False
        
        for trip in trips:
            if trip.get('id') == trip_id:
                trip['status'] = status
                if location:
                    trip['current_location'] = location
                    trip['last_updated'] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            self._save_json(self.trips_file, trips)
            logger.info(f"Updated trip {trip_id} status to {status}")
        else:
            logger.warning(f"Trip {trip_id} not found for status update")
    
    def get_active_trips(self):
        """Get all active trips"""
        trips = self._load_json(self.trips_file)
        return [t for t in trips if t.get('status') in ['pending', 'accepted', 'in_progress']]
    
    # ========== LOAD OPERATIONS ==========
    
    def create_load_request(self, load_data):
        """Create a new load request"""
        loads = self._load_json(self.loads_file)
        
        # Generate load ID
        load_id = f"LOAD{len(loads) + 1:03d}"
        load_data['id'] = load_id
        load_data['created_at'] = datetime.now().isoformat()
        load_data['status'] = 'pending'
        
        loads.append(load_data)
        self._save_json(self.loads_file, loads)
        
        logger.info(f"Created load {load_id}")
        return load_data
    
    def get_pending_loads(self):
        """Get all pending loads"""
        loads = self._load_json(self.loads_file)
        return [l for l in loads if l.get('status') == 'pending']
    
    def update_load_status(self, load_id, status, trip_id=None):
        """Update load status"""
        loads = self._load_json(self.loads_file)
        updated = False
        
        for load in loads:
            if load.get('id') == load_id:
                load['status'] = status
                if trip_id:
                    load['trip_id'] = trip_id
                updated = True
                break
        
        if updated:
            self._save_json(self.loads_file, loads)
            logger.info(f"Updated load {load_id} status to {status}")
        else:
            logger.warning(f"Load {load_id} not found for status update")
    
    def get_all_loads(self):
        """Get all loads"""
        return self._load_json(self.loads_file)

# Global database instance
db = Database()