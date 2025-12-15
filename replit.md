# Restaurant Queue Management System

## Overview

This is a modern, AI-assisted queue management platform designed to streamline restaurant operations. The system provides digital queue management capabilities with real-time status updates, AI-powered wait time predictions, SMS notifications, and comprehensive analytics. It's built as a scalable CRUD-based foundation that can be extended with advanced features like customer behavior analysis and peak hour insights.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Single Page Application (SPA)**: Uses vanilla JavaScript with tab-based navigation for a responsive user experience
- **UI Framework**: Bootstrap 5 for responsive design and consistent styling
- **Real-time Updates**: JavaScript-based polling system for live queue status updates
- **Visualization**: Chart.js integration for analytics dashboards and data visualization
- **Responsive Design**: Mobile-first approach with FontAwesome icons and custom CSS styling

### Backend Architecture
- **Web Framework**: Flask (Python) with minimal configuration for rapid development
- **API Design**: RESTful endpoints following standard HTTP methods (GET, POST, PUT, DELETE)
- **Session Management**: Flask session handling with configurable secret keys
- **Proxy Support**: Werkzeug ProxyFix middleware for deployment behind reverse proxies
- **Error Handling**: Comprehensive logging system with configurable log levels

### Data Management
- **Current State**: Mock data implementation for UI demonstration and testing
- **Queue Structure**: Standardized data models for customers with fields like queue_number, customer_name, phone, party_size, queue_type, status, timestamp, and estimated_wait
- **Status Workflow**: Three-state system (Waiting → Seated → Done) for tracking customer journey
- **Queue Types**: Separate handling for Table (dine-in) and Takeaway orders

### Core Features
- **CRUD Operations**: Complete customer lifecycle management (Add, View, Update, Delete)
- **Search Functionality**: Real-time search by customer name or phone number
- **Queue Filtering**: Dynamic filtering by queue type and status
- **Wait Time Estimation**: AI-powered predictions based on queue length and average service time
- **Status Management**: Real-time status updates with visual indicators

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: UI framework for responsive design and component styling
- **FontAwesome 6.4.0**: Icon library for consistent visual elements
- **Chart.js**: Data visualization library for analytics dashboards

### Backend Dependencies
- **Flask**: Lightweight Python web framework for API development
- **Werkzeug**: WSGI utilities including ProxyFix middleware

### Planned Integrations
- **Database System**: MySQL for production deployment (currently using mock data)
- **SMS Service**: Third-party SMS API for customer notifications
- **AI/ML Services**: Python-based machine learning models for wait time prediction
- **Analytics Platform**: Customer behavior tracking and business intelligence features

### Development Tools
- **Python Logging**: Built-in logging system for debugging and monitoring
- **Environment Configuration**: Environment variable support for sensitive data
- **WSGI Compatibility**: Production-ready deployment configuration