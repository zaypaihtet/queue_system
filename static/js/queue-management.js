// Restaurant Queue Management System JavaScript

class QueueManager {
    constructor() {
        this.queue = [];
        this.nextQueueNumber = 1;
        this.currentFilter = 'all';
        this.charts = {};
        this.aiInsights = {};
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.initializeCharts();
        this.startRealTimeUpdates();
    }

    bindEvents() {
        // Tab navigation
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Add customer form
        document.getElementById('add-customer-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addCustomer();
        });

        // Queue type filter
        document.querySelectorAll('[data-queue-type]').forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                this.filterQueue(e.target.dataset.queueType);
            });
        });

        // Search functionality
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.searchQueue(e.target.value);
        });

        // Notify customer modal
        document.getElementById('notify-customer').addEventListener('click', () => {
            this.sendNotification();
        });
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        const tabElement = document.querySelector(`[data-tab="${tabName}"]`);
        if (tabElement) {
            tabElement.classList.add('active');
        }

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        const tabContentElement = document.getElementById(`${tabName}-tab`);
        if (tabContentElement) {
            tabContentElement.classList.add('active');
        }

        // Refresh data for the active tab
        if (tabName === 'analytics') {
            this.loadAnalytics();
        }
    }

    loadInitialData() {
        // Load queue data from database
        this.loadQueueFromDatabase();
    }

    async loadQueueFromDatabase() {
        try {
            const response = await fetch('/api/queue', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (response.ok) {
                this.queue = await response.json();
                console.log('Queue data loaded successfully:', this.queue);
                this.updateAllDisplays();
            } else {
                console.error('Failed to load queue data. Status:', response.status, response.statusText);
                this.queue = [];
                this.updateAllDisplays();
            }
        } catch (error) {
            console.error('Error loading queue:', error.message || error);
            console.error('Full error:', error);
            this.queue = [];
            this.updateAllDisplays();
        }
    }

    async addCustomerToDatabase(customerData) {
        try {
            const response = await fetch('/api/customers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    customer_name: customerData.customerName,
                    phone: customerData.phone,
                    party_size: customerData.partySize,
                    queue_type: customerData.queueType
                })
            });

            return await response.json();
        } catch (error) {
            console.error('Error adding customer to database:', error);
            throw error;
        }
    }

    addCustomer() {
        const form = document.getElementById('add-customer-form');
        const formData = new FormData(form);
        
        const customer = {
            id: Date.now(),
            queueNumber: this.generateQueueNumber(formData.get('queue-type')),
            customerName: formData.get('customer-name') || document.getElementById('customer-name').value,
            phone: formData.get('customer-phone') || document.getElementById('customer-phone').value,
            partySize: parseInt(document.getElementById('party-size').value),
            queueType: document.querySelector('input[name="queue-type"]:checked').value,
            status: 'Waiting',
            timestamp: new Date(),
            estimatedWait: this.calculateEstimatedWait(formData.get('queue-type'))
        };

        // Validate required fields
        if (!customer.customerName || !customer.phone || !customer.partySize || !customer.queueType) {
            this.showToast('Please fill in all required fields', 'error');
            return;
        }

        // Send customer data to backend for AI prediction and database storage
        this.addCustomerToDatabase(customer).then(response => {
            if (response.success) {
                this.loadQueueFromDatabase();
                form.reset();
                
                const aiIndicator = response.prediction?.ai_powered ? ' 🤖' : '';
                this.showToast(`Customer ${customer.customerName} added to queue (${response.queue_number})${aiIndicator}`);
            } else {
                this.showToast('Error adding customer: ' + response.error, 'error');
            }
        }).catch(error => {
            console.error('Error adding customer:', error);
            this.showToast('Error adding customer to queue', 'error');
        });
    }

    generateQueueNumber(queueType) {
        const prefix = queueType === 'Table' ? 'T' : 'K';
        const number = String(this.nextQueueNumber++).padStart(3, '0');
        return `${prefix}${number}`;
    }

    calculateEstimatedWait(queueType) {
        const waitingCustomers = this.queue.filter(c => 
            c.status === 'Waiting' && c.queueType === queueType
        ).length;
        
        const baseTime = queueType === 'Table' ? 20 : 15; // minutes
        return baseTime + (waitingCustomers * 5);
    }

    async predictWaitTimeWithAI(customerData) {
        try {
            const response = await fetch('/api/predict-wait-time', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    queue_data: this.queue.map(c => ({
                        id: c.id,
                        party_size: c.partySize,
                        queue_type: c.queueType,
                        status: c.status,
                        timestamp: c.timestamp
                    })),
                    customer_data: {
                        party_size: customerData.partySize,
                        queue_type: customerData.queueType
                    }
                })
            });

            if (!response.ok) {
                throw new Error('AI prediction failed');
            }

            return await response.json();
        } catch (error) {
            console.error('AI prediction error:', error);
            throw error;
        }
    }

    async loadQueueInsights() {
        try {
            const response = await fetch('/api/queue-insights', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    queue_data: this.queue.map(c => ({
                        id: c.id,
                        party_size: c.partySize,
                        queue_type: c.queueType,
                        status: c.status,
                        timestamp: c.timestamp
                    }))
                })
            });

            if (response.ok) {
                this.aiInsights = await response.json();
                this.updateInsightsDisplay();
            }
        } catch (error) {
            console.error('Queue insights error:', error);
        }
    }

    async updateStatus(customerId, newStatus) {
        try {
            const response = await fetch('/api/customers/' + customerId + '/status', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    customer_id: customerId,
                    status: newStatus
                })
            });

            const result = await response.json();
            if (result.success) {
                this.loadQueueFromDatabase();
                const customer = this.queue.find(c => c.id === customerId);
                const customerName = customer ? customer.customerName : 'Customer';
                this.showToast(`Status updated to ${newStatus} for ${customerName}`);
            } else {
                this.showToast('Error updating status', 'error');
            }
        } catch (error) {
            console.error('Error updating status:', error);
            this.showToast('Error updating customer status', 'error');
        }
    }

    async removeCustomer(customerId) {
        try {
            const customer = this.queue.find(c => c.id === customerId);
            const customerName = customer ? customer.customerName : 'Customer';

            const response = await fetch('/api/customers/' + customerId, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                this.loadQueueFromDatabase();
                this.showToast(`${customerName} removed from queue`);
            } else {
                this.showToast('Error removing customer', 'error');
            }
        } catch (error) {
            console.error('Error removing customer:', error);
            this.showToast('Error removing customer from queue', 'error');
        }
    }

    filterQueue(queueType) {
        this.currentFilter = queueType;
        
        // Update active filter button
        document.querySelectorAll('[data-queue-type]').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeButton = document.querySelector(`[data-queue-type="${queueType}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
        
        this.updateQueueDisplay();
    }

    async searchQueue(searchTerm) {
        try {
            if (!searchTerm.trim()) {
                this.updateQueueDisplay();
                return;
            }

            const response = await fetch('/api/customers/search?q=' + encodeURIComponent(searchTerm));
            if (response.ok) {
                const filteredQueue = await response.json();
                this.updateQueueDisplay(filteredQueue);
            } else {
                console.error('Search failed');
                this.updateQueueDisplay([]);
            }
        } catch (error) {
            console.error('Error searching:', error);
            this.updateQueueDisplay([]);
        }
    }

    updateAllDisplays() {
        this.updateDashboardStats();
        this.updateQueueDisplay();
        this.updateMainQueueDisplay();
    }

    updateDashboardStats() {
        const waitingCount = this.queue.filter(c => c.status === 'Waiting').length;
        const seatedCount = this.queue.filter(c => c.status === 'Seated').length;
        const avgWaitTime = this.calculateAverageWaitTime();
        const todayTotal = this.queue.length;

        document.getElementById('waiting-count').textContent = waitingCount;
        document.getElementById('seated-count').textContent = seatedCount;
        document.getElementById('avg-wait-time').textContent = avgWaitTime;
        document.getElementById('today-total').textContent = todayTotal;
    }

    calculateAverageWaitTime() {
        const waitingCustomers = this.queue.filter(c => c.status === 'Waiting');
        if (waitingCustomers.length === 0) return 0;
        
        const totalWaitTime = waitingCustomers.reduce((sum, c) => sum + c.estimatedWait, 0);
        return Math.round(totalWaitTime / waitingCustomers.length);
    }

    updateQueueDisplay(customQueue = null) {
        const queueToDisplay = customQueue || this.getFilteredQueue();
        const tbody = document.getElementById('queue-tbody');
        
        if (queueToDisplay.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4">
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <div>No customers in queue</div>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = queueToDisplay.map(customer => `
            <tr>
                <td><span class="queue-number">${customer.queueNumber}</span></td>
                <td>
                    <div class="customer-info">
                        <span class="customer-name">${customer.customerName}</span>
                        <span class="customer-phone">${customer.phone}</span>
                    </div>
                </td>
                <td>${customer.partySize}</td>
                <td>
                    <span class="queue-type-${customer.queueType.toLowerCase()}">
                        <i class="fas fa-${customer.queueType === 'Table' ? 'chair' : 'shopping-bag'}"></i>
                        ${customer.queueType}
                    </span>
                </td>
                <td>
                    <span class="status-badge status-${customer.status.toLowerCase()}">
                        <i class="fas fa-${this.getStatusIcon(customer.status)}"></i>
                        ${customer.status}
                    </span>
                </td>
                <td>
                    <span class="wait-time ${this.getWaitTimeClass(customer.estimatedWait)}">
                        ${customer.estimatedWait} min
                        ${customer.aiPowered ? '<i class="fas fa-robot text-primary ms-1" title="AI Predicted"></i>' : ''}
                    </span>
                    ${customer.confidence ? `<div class="text-muted small">Confidence: ${customer.confidence}%</div>` : ''}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${customer.status === 'Waiting' ? `
                            <button class="btn btn-success btn-action" onclick="queueManager.updateStatus(${customer.id}, 'Seated')">
                                <i class="fas fa-chair"></i>
                            </button>
                        ` : ''}
                        ${customer.status === 'Seated' ? `
                            <button class="btn btn-primary btn-action" onclick="queueManager.updateStatus(${customer.id}, 'Done')">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-info btn-action" onclick="queueManager.showCustomerDetails(${customer.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-danger btn-action" onclick="queueManager.removeCustomer(${customer.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    updateMainQueueDisplay() {
        const tbody = document.getElementById('main-queue-tbody');
        const filteredQueue = this.getFilteredQueue();
        
        if (filteredQueue.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <div>No customers in selected queue</div>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = filteredQueue.map(customer => `
            <tr>
                <td><span class="queue-number">${customer.queueNumber}</span></td>
                <td>
                    <div class="customer-info">
                        <span class="customer-name">${customer.customerName}</span>
                        <span class="customer-phone">${customer.phone}</span>
                    </div>
                </td>
                <td>${customer.partySize} ${customer.partySize === 1 ? 'person' : 'people'}</td>
                <td>
                    <span class="queue-type-${customer.queueType.toLowerCase()}">
                        <i class="fas fa-${customer.queueType === 'Table' ? 'chair' : 'shopping-bag'}"></i>
                        ${customer.queueType}
                    </span>
                </td>
                <td>
                    <span class="status-badge status-${customer.status.toLowerCase()}">
                        <i class="fas fa-${this.getStatusIcon(customer.status)}"></i>
                        ${customer.status}
                    </span>
                </td>
                <td>
                    <span class="wait-time ${this.getWaitTimeClass(customer.estimatedWait)}">
                        ${customer.estimatedWait} min
                        ${customer.aiPowered ? '<i class="fas fa-robot text-primary ms-1" title="AI Predicted"></i>' : ''}
                    </span>
                    ${customer.confidence ? `<div class="text-muted small">Confidence: ${customer.confidence}%</div>` : ''}
                </td>
                <td>${this.safeFormatTime(customer.timestamp)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${customer.status === 'Waiting' ? `
                            <button class="btn btn-success btn-action" onclick="queueManager.updateStatus(${customer.id}, 'Seated')" title="Mark as Seated">
                                <i class="fas fa-chair"></i>
                            </button>
                        ` : ''}
                        ${customer.status === 'Seated' ? `
                            <button class="btn btn-primary btn-action" onclick="queueManager.updateStatus(${customer.id}, 'Done')" title="Mark as Done">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                        <button class="btn btn-info btn-action" onclick="queueManager.showCustomerDetails(${customer.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-warning btn-action" onclick="queueManager.sendSMSNotification(${customer.id})" title="Send SMS">
                            <i class="fas fa-sms"></i>
                        </button>
                        <button class="btn btn-secondary btn-action" onclick="queueManager.showQRCode(${customer.id})" title="Show QR Code">
                            <i class="fas fa-qrcode"></i>
                        </button>
                        <button class="btn btn-danger btn-action" onclick="queueManager.removeCustomer(${customer.id})" title="Remove">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    getFilteredQueue() {
        if (this.currentFilter === 'all') {
            return this.queue;
        }
        return this.queue.filter(customer => customer.queueType === this.currentFilter);
    }

    getStatusIcon(status) {
        const icons = {
            'Waiting': 'clock',
            'Seated': 'user-check',
            'Done': 'check-circle'
        };
        return icons[status] || 'question';
    }

    getWaitTimeClass(waitTime) {
        if (waitTime <= 15) return 'comfortable';
        if (waitTime <= 30) return 'moderate';
        return 'urgent';
    }

    safeFormatTime(timestamp) {
        try {
            // Convert string timestamp to Date object if needed
            const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
            return date.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });
        } catch (error) {
            console.error('Error formatting timestamp:', timestamp, error);
            return 'N/A';
        }
    }

    formatTime(timestamp) {
        return this.safeFormatTime(timestamp);
    }

    async showQRCode(customerId) {
        try {
            const response = await fetch(`/api/customer/${customerId}/qr`);
            if (!response.ok) {
                throw new Error('Failed to generate QR code');
            }
            
            const qrData = await response.json();
            const customer = this.queue.find(c => c.id === customerId);
            
            // Create and show QR code modal
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-qrcode me-2"></i>
                                Customer QR Code
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <div class="mb-3">
                                <h6>Queue Number: <span class="badge bg-primary">${qrData.queue_number}</span></h6>
                                <small class="text-muted">${customer ? customer.customerName : 'Customer'}</small>
                            </div>
                            <div class="qr-code-container mb-3">
                                <img src="${qrData.qr_code}" alt="QR Code" class="img-fluid" style="max-width: 200px; border: 2px solid #dee2e6; border-radius: 10px;">
                            </div>
                            <div class="alert alert-info">
                                <small>
                                    <i class="fas fa-info-circle me-1"></i>
                                    Customers can scan this QR code to check their queue status and wait time.
                                </small>
                            </div>
                            <div class="mb-2">
                                <small class="text-muted">Direct link:</small><br>
                                <code style="font-size: 0.8em; word-break: break-all;">${qrData.status_url}</code>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-primary" onclick="navigator.clipboard.writeText('${qrData.status_url}').then(() => this.textContent = 'Copied!')">
                                <i class="fas fa-copy me-1"></i>
                                Copy Link
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Remove modal from DOM when hidden
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
            
        } catch (error) {
            console.error('Error showing QR code:', error);
            alert('Failed to generate QR code. Please try again.');
        }
    }

    showCustomerDetails(customerId) {
        const customer = this.queue.find(c => c.id === customerId);
        if (!customer) return;

        const detailsHTML = `
            <div class="row">
                <div class="col-sm-4 font-weight-bold">Queue Number:</div>
                <div class="col-sm-8">${customer.queueNumber}</div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Customer Name:</div>
                <div class="col-sm-8">${customer.customerName}</div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Phone:</div>
                <div class="col-sm-8">${customer.phone}</div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Party Size:</div>
                <div class="col-sm-8">${customer.partySize} ${customer.partySize === 1 ? 'person' : 'people'}</div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Queue Type:</div>
                <div class="col-sm-8">${customer.queueType}</div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Status:</div>
                <div class="col-sm-8">
                    <span class="status-badge status-${customer.status.toLowerCase()}">
                        <i class="fas fa-${this.getStatusIcon(customer.status)}"></i>
                        ${customer.status}
                    </span>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Entry Time:</div>
                <div class="col-sm-8">${new Date(customer.timestamp).toLocaleString()}</div>
            </div>
            <div class="row mt-2">
                <div class="col-sm-4 font-weight-bold">Estimated Wait:</div>
                <div class="col-sm-8">
                    <span class="wait-time ${this.getWaitTimeClass(customer.estimatedWait)}">
                        ${customer.estimatedWait} minutes
                    </span>
                </div>
            </div>
        `;

        document.getElementById('customer-details').innerHTML = detailsHTML;
        
        // Store customer ID for notification
        document.getElementById('notify-customer').dataset.customerId = customerId;
        
        const modal = new bootstrap.Modal(document.getElementById('customerModal'));
        modal.show();
    }

    // New function to call the backend
    async sendSMS(smsData) {
        try {
            const response = await fetch('/send_sms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(smsData),
            });
            return await response.json();
        } catch (error) {
            console.error('Error sending SMS via fetch:', error);
            return { status: 'error', message: 'Frontend fetch error' };
        }
    }

    async sendSMSNotification(customerId) {
        const customer = this.queue.find(c => c.id === customerId);
        if (!customer) {
            this.showToast('Customer not found', 'error');
            return;
        }

        const smsData = {
            to: customer.phone.startsWith('66') ? customer.phone : '66' + customer.phone.replace(/^0/, ''),
            message: `Hello ${customer.customerName}, your table/queue number ${customer.queueNumber} is ready. Please proceed to the counter.`
        };

        try {
            const result = await this.sendSMS(smsData);
            if (result.status === 'success') {
                this.showToast(`SMS sent to ${customer.customerName} (${customer.phone})`);
            } else {
                this.showToast(`SMS failed: ${result.message || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.showToast('Error sending SMS', 'error');
        }
    }

    sendNotification() {
        const customerId = document.getElementById('notify-customer').dataset.customerId;
        if (customerId) {
            this.sendSMSNotification(parseInt(customerId));
            bootstrap.Modal.getInstance(document.getElementById('customerModal')).hide();
        }
    }

    loadAnalytics() {
        // Mock analytics data
        const analytics = {
            todayCustomers: this.queue.length,
            averageWaitTime: this.calculateAverageWaitTime(),
            peakHour: '12:00 PM',
            queueEfficiency: 87,
            hourlyData: [5, 8, 12, 18, 25, 30, 35, 42, 38, 28, 15, 10],
            waitTimeData: [15, 20, 18, 22, 16, 19, 21, 17, 14, 25, 23, 18]
        };

        // Update analytics cards
        document.getElementById('analytics-today').textContent = analytics.todayCustomers;
        document.getElementById('analytics-wait').textContent = analytics.averageWaitTime;
        document.getElementById('analytics-peak').textContent = analytics.peakHour;
        document.getElementById('analytics-efficiency').textContent = analytics.queueEfficiency;

        // Update charts
        this.updateCharts(analytics);
        
        // Load AI insights for analytics
        this.loadQueueInsights();
    }

    initializeCharts() {
        // Hourly Customer Flow Chart
        const hourlyCtx = document.getElementById('hourly-chart').getContext('2d');
        this.charts.hourlyChart = new Chart(hourlyCtx, {
            type: 'line',
            data: {
                labels: ['6AM', '7AM', '8AM', '9AM', '10AM', '11AM', '12PM', '1PM', '2PM', '3PM', '4PM', '5PM'],
                datasets: [{
                    label: 'Customers',
                    data: [],
                    borderColor: 'rgb(78, 115, 223)',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Customer Flow Throughout the Day'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Wait Time Chart
        const waitCtx = document.getElementById('wait-time-chart').getContext('2d');
        this.charts.waitTimeChart = new Chart(waitCtx, {
            type: 'doughnut',
            data: {
                labels: ['< 15 min', '15-30 min', '> 30 min'],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(28, 200, 138, 0.8)',
                        'rgba(246, 194, 62, 0.8)',
                        'rgba(231, 74, 59, 0.8)'
                    ],
                    borderColor: [
                        'rgb(28, 200, 138)',
                        'rgb(246, 194, 62)',
                        'rgb(231, 74, 59)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Wait Time Distribution'
                    }
                }
            }
        });
    }

    updateCharts(analytics) {
        // Update hourly chart
        this.charts.hourlyChart.data.datasets[0].data = analytics.hourlyData;
        this.charts.hourlyChart.update();

        // Update wait time distribution
        const waitTimes = this.queue.map(c => c.estimatedWait);
        const shortWait = waitTimes.filter(t => t < 15).length;
        const mediumWait = waitTimes.filter(t => t >= 15 && t <= 30).length;
        const longWait = waitTimes.filter(t => t > 30).length;

        this.charts.waitTimeChart.data.datasets[0].data = [shortWait, mediumWait, longWait];
        this.charts.waitTimeChart.update();
    }

    startRealTimeUpdates() {
        // Refresh queue data from database periodically
        setInterval(() => {
            this.loadQueueFromDatabase();
        }, 30000); // Update every 30 seconds
    }

    showToast(message, type = 'success') {
        const toast = document.getElementById('success-toast');
        const toastMessage = document.getElementById('toast-message');
        
        toastMessage.textContent = message;
        
        // Change toast style based on type
        const toastHeader = toast.querySelector('.toast-header');
        if (type === 'error') {
            toastHeader.className = 'toast-header bg-danger text-white';
            toastHeader.querySelector('i').className = 'fas fa-exclamation-circle me-2';
        } else {
            toastHeader.className = 'toast-header bg-success text-white';
            toastHeader.querySelector('i').className = 'fas fa-check-circle me-2';
        }
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    updateInsightsDisplay() {
        if (!this.aiInsights || Object.keys(this.aiInsights).length === 0) return;

        // Update efficiency score in analytics
        if (this.aiInsights.efficiency_score) {
            document.getElementById('analytics-efficiency').textContent = this.aiInsights.efficiency_score;
        }

        // Add AI insights section to analytics tab if it doesn't exist
        let insightsSection = document.getElementById('ai-insights-section');
        if (!insightsSection) {
            const analyticsTab = document.getElementById('analytics-tab');
            const insightsHTML = `
                <div id="ai-insights-section" class="row mt-4">
                    <div class="col-12">
                        <div class="card shadow">
                            <div class="card-header py-3">
                                <h6 class="m-0 font-weight-bold text-primary">
                                    <i class="fas fa-robot me-2"></i>AI Queue Insights
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6 class="text-muted">Current Bottlenecks:</h6>
                                        <ul id="ai-bottlenecks" class="list-unstyled">
                                            <!-- Bottlenecks will be populated here -->
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h6 class="text-muted">AI Recommendations:</h6>
                                        <ul id="ai-suggestions" class="list-unstyled">
                                            <!-- Suggestions will be populated here -->
                                        </ul>
                                    </div>
                                </div>
                                <div class="mt-3">
                                    <h6 class="text-muted">Peak Hour Prediction:</h6>
                                    <p id="ai-peak-prediction" class="mb-0">
                                        <!-- Peak prediction will be populated here -->
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            analyticsTab.insertAdjacentHTML('beforeend', insightsHTML);
        }

        // Update bottlenecks
        const bottlenecksList = document.getElementById('ai-bottlenecks');
        if (bottlenecksList && this.aiInsights.bottlenecks) {
            bottlenecksList.innerHTML = this.aiInsights.bottlenecks.map(bottleneck => 
                `<li><i class="fas fa-exclamation-triangle text-warning me-2"></i>${bottleneck}</li>`
            ).join('');
        }

        // Update suggestions
        const suggestionsList = document.getElementById('ai-suggestions');
        if (suggestionsList && this.aiInsights.suggestions) {
            suggestionsList.innerHTML = this.aiInsights.suggestions.map(suggestion => 
                `<li><i class="fas fa-lightbulb text-info me-2"></i>${suggestion}</li>`
            ).join('');
        }

        // Update peak prediction
        const peakPrediction = document.getElementById('ai-peak-prediction');
        if (peakPrediction && this.aiInsights.peak_hour_prediction) {
            peakPrediction.textContent = this.aiInsights.peak_hour_prediction;
        }
    }
}

// Initialize the queue manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.queueManager = new QueueManager();
});
