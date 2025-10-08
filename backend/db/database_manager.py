import sqlite3
import json
from device.utils.logger import get_logger


class DatabaseManager:
    def __init__(self,db_path):
        self.db_path = db_path
        self.logger = get_logger("DatabaseManager")
        self.logger.info(f"Initializing DatabaseManager with path: {db_path}")
        self._test_connection()

        self._test_connection()

    def _test_connection(self):
        """Test database connection and log status"""
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            sqlconn.close()
            self.logger.info(f"Database connection successful. Found {table_count} tables")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def insert_object(self,object_id,object_type):
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("""INSERT INTO object (object_id,type) VALUES (?,?)""", (object_id,object_type))
            sqlconn.commit()
            sqlconn.close()
            self.logger.debug(f"Object inserted successfully: ID={object_id}, Type={object_type}")
        except Exception as e:
            self.logger.error(f"Failed to insert object: {e}")
            raise


    def insert_events(self,object_id,zone_id,location_id,has_helmet,has_vest,time):
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("""INSERT INTO events (object_id,zone_id,location_id,has_helmet,has_vest,time)
            VALUES (?,?,?,?,?,?)""",
            (object_id,zone_id,location_id,has_helmet,has_vest,time))
            event_id = cursor.lastrowid
            sqlconn.commit()
            sqlconn.close()
            self.logger.info(f"Event inserted: ID={event_id}, Object={object_id}, Helmet={has_helmet}, Vest={has_vest}")
        except Exception as e:
            self.logger.error(f"Failed to insert event: {e}")
            raise


    def get_event(self):
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("SELECT * from events")
            rows = cursor.fetchall()
            sqlconn.close()
            self.logger.debug(f"Retrieved {len(rows)} events from database")
            return rows
        except Exception as e:
            self.logger.error(f"Failed to retrieve events: {e}")
            raise

    def insert_zone(self, points, name, location_id):
        try:
            coords_json = json.dumps(points)
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("""INSERT INTO zones (coords,name,location_id) VALUES (?,?,?)""", (coords_json, name, location_id))
            zone_id = cursor.lastrowid
            sqlconn.commit()
            sqlconn.close()
            self.logger.info(f"Zone inserted: ID={zone_id}, Name={name}, Location={location_id}")
        except Exception as e:
            self.logger.error(f"Failed to insert zone: {e}")
            raise

    def insert_location(self, name):
        """Insert a new location and return its ID"""
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("""INSERT INTO location (name) VALUES (?)""", (name,))
            location_id = cursor.lastrowid
            sqlconn.commit()
            sqlconn.close()
            self.logger.info(f"Location inserted: ID={location_id}, Name={name}")
            return location_id
        except Exception as e:
            self.logger.error(f"Failed to insert location: {e}")
            raise

    def get_location_by_name(self, name):
        """Get location by name, return location_id if exists"""
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("SELECT location_id FROM location WHERE name = ?", (name,))
            result = cursor.fetchone()
            sqlconn.close()
            if result:
                self.logger.debug(f"Found location: {name} with ID {result[0]}")
            else:
                self.logger.debug(f"Location not found: {name}")
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get location by name: {e}")
            raise

    def fetch_all_zones(self):
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("SELECT * from zones")
            rows = cursor.fetchall()
            sqlconn.close()

            zones = []
            for row in rows:
                zone_id,location_id,coords_json,name = row
                coords = json.loads(coords_json)
                zones.append({"zone_id":zone_id,"location_id":location_id,"coords":coords,"name":name})
            
            self.logger.debug(f"Retrieved {len(zones)} zones from database")
            return zones
        except Exception as e:
            self.logger.error(f"Failed to fetch zones: {e}")
            raise

    def set_ai_running(self,value: bool):
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("UPDATE system_config SET ai_running=? WHERE system_config_id=1",(1 if value else 0,))
            sqlconn.commit()
            sqlconn.close()
            self.logger.info(f"AI running status updated to: {value}")
        except Exception as e:
            self.logger.error(f"Failed to set AI running status: {e}")
            raise

    def get_ai_running(self) -> bool:
        try:
            sqlconn = sqlite3.connect(self.db_path)
            cursor = sqlconn.cursor()
            cursor.execute("SELECT ai_running FROM system_config WHERE system_config_id=1")
            result = cursor.fetchone()
            sqlconn.close()
            if result:
                status = result[0] == 1
                self.logger.debug(f"AI running status retrieved: {status}")
                return status
            self.logger.warning("No system config found, defaulting to False")
            return False
        except Exception as e:
            self.logger.error(f"Failed to get AI running status: {e}")
            return False
