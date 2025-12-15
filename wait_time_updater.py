"""
Real-time wait time updater module
Provides functions to automatically recalculate wait times when queue changes occur
"""

from models import Customer, DatabaseManager
from datetime import datetime

class WaitTimeUpdater:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.customer_model = Customer(db_manager)
    
    def update_all_wait_times(self):
        """Recalculate and update wait times for all waiting customers"""
        return self.customer_model.recalculate_wait_times()
    
    def get_real_time_wait_estimate(self, queue_type: str, party_size: int = 1) -> int:
        """Get real-time wait estimate for a new customer"""
        waiting_customers = self.customer_model.get_by_status('Waiting')
        
        # Count customers ahead in the same queue type
        customers_ahead = len([c for c in waiting_customers if c['queue_type'] == queue_type])
        
        # Calculate base wait time
        if queue_type == 'Table':
            base_wait = 15  # Base wait for table service
            per_customer = 8  # Additional minutes per customer ahead
        else:  # Takeaway
            base_wait = 10  # Base wait for takeaway
            per_customer = 3  # Additional minutes per customer ahead
        
        # Calculate estimated wait time
        estimated_wait = base_wait + (customers_ahead * per_customer)
        
        # Adjust for party size (larger parties may take longer)
        if party_size > 4:
            estimated_wait += 5
        
        return max(estimated_wait, 5)  # Minimum 5 minutes wait
    
    def trigger_wait_time_update(self, event_type: str = 'queue_change'):
        """Trigger wait time updates when queue changes occur"""
        try:
            # Recalculate wait times for all waiting customers
            success = self.update_all_wait_times()
            
            if success:
                print(f"Wait times updated successfully due to: {event_type}")
            else:
                print(f"Failed to update wait times for event: {event_type}")
                
            return success
        except Exception as e:
            print(f"Error updating wait times: {e}")
            return False