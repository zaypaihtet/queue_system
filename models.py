import sqlite3
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='queue_management.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup and retry logic"""
        conn = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=20.0)
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                yield conn
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise
            finally:
                if conn:
                    conn.close()
    
    def init_database(self):
        """Initialize the database and create tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA synchronous=NORMAL')
            cursor.execute('PRAGMA cache_size=1000')
            cursor.execute('PRAGMA temp_store=MEMORY')
            
            # Create customers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_number TEXT UNIQUE NOT NULL,
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    party_size INTEGER NOT NULL,
                    queue_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Waiting',
                    estimated_wait INTEGER NOT NULL,
                    confidence INTEGER DEFAULT NULL,
                    ai_powered BOOLEAN DEFAULT FALSE,
                    ai_factors TEXT DEFAULT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create analytics table for historical data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_customers INTEGER DEFAULT 0,
                    avg_wait_time REAL DEFAULT 0,
                    peak_hour TEXT DEFAULT NULL,
                    efficiency_score INTEGER DEFAULT 0,
                    hourly_data TEXT DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

class Customer:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create(self, queue_number: str, customer_name: str, phone: str, 
               party_size: int, queue_type: str, estimated_wait: int,
               confidence: Optional[int] = None, ai_powered: bool = False,
               ai_factors: Optional[List[str]] = None) -> int:
        """Create a new customer record"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            ai_factors_json = json.dumps(ai_factors) if ai_factors else None
            
            cursor.execute('''
                INSERT INTO customers 
                (queue_number, customer_name, phone, party_size, queue_type, 
                 estimated_wait, confidence, ai_powered, ai_factors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (queue_number, customer_name, phone, party_size, queue_type,
                  estimated_wait, confidence, ai_powered, ai_factors_json))
            
            customer_id = cursor.lastrowid or 0
            conn.commit()
            return customer_id
    
    def get_all(self) -> List[Dict]:
        """Get all customers"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM customers 
                ORDER BY created_at ASC
            ''')
            
            customers = []
            for row in cursor.fetchall():
                customer = dict(row)
                # Parse AI factors if they exist
                if customer['ai_factors']:
                    customer['ai_factors'] = json.loads(customer['ai_factors'])
                customers.append(customer)
            
            return customers
    
    def get_by_id(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            
            if row:
                customer = dict(row)
                if customer['ai_factors']:
                    customer['ai_factors'] = json.loads(customer['ai_factors'])
                return customer
            
            return None
    
    def update_status(self, customer_id: int, status: str) -> bool:
        """Update customer status"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE customers 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (status, customer_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def update_wait_time(self, customer_id: int, estimated_wait: int, 
                        confidence: Optional[int] = None, ai_powered: bool = False,
                        ai_factors: Optional[List[str]] = None) -> bool:
        """Update customer wait time"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            ai_factors_json = json.dumps(ai_factors) if ai_factors else None
            
            cursor.execute('''
                UPDATE customers 
                SET estimated_wait = ?, confidence = ?, ai_powered = ?, 
                    ai_factors = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (estimated_wait, confidence, ai_powered, ai_factors_json, customer_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def delete(self, customer_id: int) -> bool:
        """Delete a customer"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
    
    def get_by_status(self, status: str) -> List[Dict]:
        """Get customers by status"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM customers 
                WHERE status = ? 
                ORDER BY created_at ASC
            ''', (status,))
            
            customers = []
            for row in cursor.fetchall():
                customer = dict(row)
                if customer['ai_factors']:
                    customer['ai_factors'] = json.loads(customer['ai_factors'])
                customers.append(customer)
            
            return customers
    
    def get_by_queue_type(self, queue_type: str) -> List[Dict]:
        """Get customers by queue type"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM customers 
                WHERE queue_type = ? 
                ORDER BY created_at ASC
            ''', (queue_type,))
            
            customers = []
            for row in cursor.fetchall():
                customer = dict(row)
                if customer['ai_factors']:
                    customer['ai_factors'] = json.loads(customer['ai_factors'])
                customers.append(customer)
            
            return customers
    
    def search(self, search_term: str) -> List[Dict]:
        """Search customers by name or phone"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM customers 
                WHERE customer_name LIKE ? OR phone LIKE ?
                ORDER BY created_at ASC
            ''', (f'%{search_term}%', f'%{search_term}%'))
            
            customers = []
            for row in cursor.fetchall():
                customer = dict(row)
                if customer['ai_factors']:
                    customer['ai_factors'] = json.loads(customer['ai_factors'])
                customers.append(customer)
            
            return customers
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total counts
            cursor.execute('SELECT COUNT(*) as total FROM customers')
            total = cursor.fetchone()['total']
            
            # Get status counts
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM customers 
                GROUP BY status
            ''')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Get average wait time
            cursor.execute('''
                SELECT AVG(estimated_wait) as avg_wait 
                FROM customers 
                WHERE status = 'Waiting'
            ''')
            avg_wait_result = cursor.fetchone()
            avg_wait = avg_wait_result['avg_wait'] if avg_wait_result['avg_wait'] else 0
            
            # Get today's customer count
            cursor.execute('''
                SELECT COUNT(*) as today_count 
                FROM customers 
                WHERE DATE(created_at) = DATE('now')
            ''')
            today_count = cursor.fetchone()['today_count']
            
            return {
                'total': total,
                'waiting': status_counts.get('Waiting', 0),
                'seated': status_counts.get('Seated', 0),
                'done': status_counts.get('Done', 0),
                'avg_wait_time': round(avg_wait, 1),
                'today_total': today_count
            }

    def recalculate_wait_times(self) -> bool:
        """Recalculate wait times for all waiting customers based on queue position"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all waiting customers ordered by creation time
            cursor.execute('''
                SELECT id, queue_type, party_size 
                FROM customers 
                WHERE status = 'Waiting' 
                ORDER BY created_at ASC
            ''')
            waiting_customers = cursor.fetchall()
            
            for i, customer in enumerate(waiting_customers):
                # Calculate wait time based on position and queue type
                position = i
                if customer['queue_type'] == 'Table':
                    base_wait = 15
                    per_customer = 8
                else:  # Takeaway
                    base_wait = 10
                    per_customer = 3
                
                # Calculate estimated wait time
                estimated_wait = base_wait + (position * per_customer)
                
                # Update the customer's wait time
                cursor.execute('''
                    UPDATE customers 
                    SET estimated_wait = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (estimated_wait, customer['id']))
            
            conn.commit()
            return True

class Analytics:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_daily_analytics(self, date: str, total_customers: int, 
                           avg_wait_time: float, peak_hour: str, 
                           efficiency_score: int, hourly_data: Dict) -> bool:
        """Save daily analytics"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            hourly_data_json = json.dumps(hourly_data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO analytics 
                (date, total_customers, avg_wait_time, peak_hour, efficiency_score, hourly_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (date, total_customers, avg_wait_time, peak_hour, efficiency_score, hourly_data_json))
            
            conn.commit()
            return True
    
    def get_analytics_by_date(self, date: str) -> Optional[Dict]:
        """Get analytics for a specific date"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM analytics WHERE date = ?', (date,))
            row = cursor.fetchone()
            
            if row:
                analytics = dict(row)
                if analytics['hourly_data']:
                    analytics['hourly_data'] = json.loads(analytics['hourly_data'])
                return analytics
            
            return None