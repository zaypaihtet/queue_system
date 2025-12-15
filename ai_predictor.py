import json
import os
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

# load .env file
load_dotenv()
# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class AIWaitTimePredictor:
    def __init__(self):
        self.historical_data = []
        self.current_hour = datetime.now().hour
        
    def predict_wait_time(self, queue_data, customer_data, restaurant_context=None):
        """
        Use AI to predict accurate wait times based on queue data and patterns
        """
        try:
            # Prepare context for AI analysis
            context = self._prepare_context(queue_data, customer_data, restaurant_context)
            
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert restaurant operations analyst specializing in queue management and wait time prediction. 
                        Analyze the provided queue data and predict accurate wait times based on:
                        - Current queue length and party sizes
                        - Time of day and typical service patterns
                        - Customer type (dine-in vs takeaway)
                        - Historical patterns and peak hours
                        - Service efficiency factors
                        
                        Respond with JSON in this exact format:
                        {
                            "estimated_wait_minutes": number,
                            "confidence_level": number (0-100),
                            "factors": ["factor1", "factor2"],
                            "recommendation": "string"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this restaurant queue data and predict wait time: {context}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content or "{}")
            
            # Validate and return prediction
            return {
                "estimated_wait": max(5, min(120, result.get("estimated_wait_minutes", 20))),
                "confidence": max(0, min(100, result.get("confidence_level", 75))),
                "factors": result.get("factors", ["Queue length", "Time of day"]),
                "recommendation": result.get("recommendation", "Standard wait time predicted"),
                "ai_powered": True
            }
            
        except Exception as e:
            print(f"AI prediction error: {e}")
            # Fallback to basic calculation
            return self._fallback_prediction(queue_data, customer_data)
    
    def _prepare_context(self, queue_data, customer_data, restaurant_context):
        """Prepare structured context for AI analysis"""
        
        current_time = datetime.now()
        
        context = {
            "current_time": {
                "hour": current_time.hour,
                "day_of_week": current_time.strftime("%A"),
                "is_peak_hour": self._is_peak_hour(current_time.hour)
            },
            "queue_analysis": {
                "total_waiting": len([c for c in queue_data if c.get('status') == 'Waiting']),
                "total_seated": len([c for c in queue_data if c.get('status') == 'Seated']),
                "avg_party_size": self._calculate_avg_party_size(queue_data),
                "queue_types": self._analyze_queue_types(queue_data)
            },
            "new_customer": {
                "party_size": customer_data.get('party_size', 2),
                "queue_type": customer_data.get('queue_type', 'Table')
            },
            "service_patterns": {
                "typical_table_service_time": "20-45 minutes",
                "typical_takeaway_time": "10-20 minutes",
                "kitchen_capacity": "moderate",
                "staff_efficiency": "good"
            }
        }
        
        if restaurant_context:
            context["restaurant_context"] = restaurant_context
            
        return json.dumps(context, indent=2)
    
    def _is_peak_hour(self, hour):
        """Determine if current hour is a peak dining time"""
        return hour in [12, 13, 18, 19, 20]  # Lunch and dinner rush
    
    def _calculate_avg_party_size(self, queue_data):
        """Calculate average party size in current queue"""
        if not queue_data:
            return 2
        
        party_sizes = [c.get('party_size', 2) for c in queue_data if c.get('status') == 'Waiting']
        return sum(party_sizes) / len(party_sizes) if party_sizes else 2
    
    def _analyze_queue_types(self, queue_data):
        """Analyze distribution of queue types"""
        table_count = len([c for c in queue_data if c.get('queue_type') == 'Table' and c.get('status') == 'Waiting'])
        takeaway_count = len([c for c in queue_data if c.get('queue_type') == 'Takeaway' and c.get('status') == 'Waiting'])
        
        return {
            "table_waiting": table_count,
            "takeaway_waiting": takeaway_count,
            "table_ratio": table_count / max(1, table_count + takeaway_count)
        }
    
    def _fallback_prediction(self, queue_data, customer_data):
        """Fallback prediction when AI is unavailable"""
        queue_type = customer_data.get('queue_type', 'Table')
        waiting_same_type = len([c for c in queue_data 
                               if c.get('queue_type') == queue_type and c.get('status') == 'Waiting'])
        
        base_time = 20 if queue_type == 'Table' else 15
        additional_time = waiting_same_type * 8
        
        return {
            "estimated_wait": base_time + additional_time,
            "confidence": 60,
            "factors": ["Queue length", "Service type"],
            "recommendation": "Standard calculation used",
            "ai_powered": False
        }
    
    def analyze_queue_efficiency(self, queue_data, historical_data=None):
        """Analyze overall queue efficiency and provide insights"""
        try:
            analysis_context = {
                "current_queue": queue_data,
                "timestamp": datetime.now().isoformat(),
                "metrics_needed": [
                    "average_wait_time",
                    "queue_efficiency_score",
                    "bottleneck_analysis",
                    "improvement_suggestions"
                ]
            }
            
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a restaurant operations expert. Analyze queue efficiency and provide actionable insights.
                        Respond with JSON in this format:
                        {
                            "efficiency_score": number (0-100),
                            "avg_wait_time": number,
                            "bottlenecks": ["bottleneck1", "bottleneck2"],
                            "suggestions": ["suggestion1", "suggestion2"],
                            "peak_hour_prediction": "string"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this restaurant queue for efficiency: {json.dumps(analysis_context, indent=2)}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content or "{}")
            
        except Exception as e:
            print(f"Queue analysis error: {e}")
            return {
                "efficiency_score": 75,
                "avg_wait_time": 20,
                "bottlenecks": ["Standard analysis unavailable"],
                "suggestions": ["Monitor queue regularly"],
                "peak_hour_prediction": "Standard patterns expected"
            }