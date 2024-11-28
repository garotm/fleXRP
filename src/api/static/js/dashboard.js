/**
 * Dashboard functionality
 */

const DashboardCharts = {
    transactionChart: null,
    volumeChart: null,

    async initialize() {
        await this.initializeTransactionChart();
        await this.initializeVolumeChart();
        this.setupRefreshInterval();
    },

    async initializeTransactionChart() {
        const ctx = document.getElementById('transactionChart').getContext('2d');
        const data = await this.fetchChartData('transactions');

        this.transactionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Transactions',
                    data: data.values,
                    borderColor: 'rgb(79, 70, 229)',
                    tension: 0.4,
                    fill: true,
                    backgroundColor: 'rgba(79, 70, 229, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    },

    async initializeVolumeChart() {
        const ctx = document.getElementById('volumeChart').getContext('2d');
        const data = await this.fetchChartData('volume');

        this.volumeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Volume (XRP)',
                    data: data.values,
                    backgroundColor: 'rgb(79, 70, 229)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    },

    async fetchChartData(type) {
        try {
            const response = await ApiClient.get(`/api/dashboard/charts/${type}`);
            return response.data;
        } catch (error) {
            console.error(`Failed to fetch ${type} chart data:`, error);
            NotificationSystem.show(
                `Failed to load ${type} chart`,
                'error'
            );
            return { labels: [], values: [] };
        }
    },

    setupRefreshInterval() {
        // Refresh charts every 5 minutes
        setInterval(async () => {
            const transactionData = await this.fetchChartData('transactions');
            const volumeData = await this.fetchChartData('volume');

            this.updateChart(this.transactionChart, transactionData);
            this.updateChart(this.volumeChart, volumeData);
        }, 300000);
    },

    updateChart(chart, newData) {
        chart.data.labels = newData.labels;
        chart.data.datasets[0].data = newData.values;
        chart.update();
    }
};

// Live transaction updates
const LiveTransactions = {
    initialize() {
        this.setupEventSource();
        this.setupTransactionList();
    },

    setupEventSource() {
        const eventSource = new EventSource('/api/transactions/live');
        
        eventSource.onmessage = (event) => {
            const transaction = JSON.parse(event.data);
            this.addTransaction(transaction);
        };

        eventSource.onerror = (error) => {
            console.error('LiveTransactions EventSource error:', error);
            eventSource.close();
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.setupEventSource(), 5000);
        };
    },

    setupTransactionList() {
        const list = document.getElementById('recent-transactions');
        if (!list) return;

        // Keep only the last 10 transactions
        while (list.children.length > 10) {
            list.removeChild(list.lastChild);
        }
    },

    addTransaction(transaction) {
        const list = document.getElementById('recent-transactions');
        if (!list) return;

        const element = this.createTransactionElement(transaction);
        
        // Add with animation
        element.classList.add('opacity-0');
        list.insertBefore(element, list.firstChild);
        
        // Trigger reflow
        element.offsetHeight;
        
        // Add animation class
        element.classList.add('transition-opacity', 'duration-500');
        element.classList.remove('opacity-0');

        // Remove oldest transaction if more than 10
        if (list.children.length > 10) {
            const oldest = list.lastChild;
            oldest.classList.add('opacity-0');
            setTimeout(() => oldest.remove(), 500);
        }
    },

    createTransactionElement(transaction) {
        const element = document.createElement('div');
        element.className = 'bg-white shadow rounded-lg p-4 mb-4';
        element.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <span class="inline-flex items-center justify-center h-8 w-8 rounded-full ${
                            transaction.type === 'received' ? 'bg-green-100' : 'bg-red-100'
                        }">
                            <svg class="h-5 w-5 ${
                                transaction.type === 'received' ? 'text-green-600' : 'text-red-600'
                            }" viewBox="0 0 20 20" fill="currentColor">
                                ${
                                    transaction.type === 'received'
                                        ? '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd" />'
                                        : '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.707-10.293a1 1 0 00-1.414 0l-3 3a1 1 0 101.414 1.414L9 11.414V15a1 1 0 102 0v-3.586l1.293 1.293a1 1 0 001.414-1.414l-3-3z" clip-rule="evenodd" />'
                                }
                            </svg>
                        </span>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-900">
                            ${transaction.type === 'received' ? 'Payment Received' : 'Payment Sent'}
                        </p>
                        <p class="text-sm text-gray-500">
                            ${new Date(transaction.timestamp).toLocaleString()}
                        </p>
                    </div>
                </div>
                <div class="ml-4">
                    <p class="text-sm font-medium text-gray-900">
                        ${transaction.amount} XRP
                    </p>
                    <p class="text-sm text-gray-500">
                        $${transaction.amount_usd}
                    </p>
                </div>
            </div>
        `;
        return element;
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    DashboardCharts.initialize();
    LiveTransactions.initialize();
}); 