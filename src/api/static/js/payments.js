/**
 * Payment functionality
 */

const PaymentManager = {
    async initialize() {
        this.setupPaymentForm();
        this.setupQRCodeGenerator();
        this.initializePaymentHistory();
    },

    setupPaymentForm() {
        const form = document.getElementById('payment-request-form');
        if (!form) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createPaymentRequest(form);
        });

        // Setup real-time currency conversion
        const amountInput = form.querySelector('[name="amount"]');
        const currencySelect = form.querySelector('[name="currency"]');
        
        if (amountInput && currencySelect) {
            const updateRate = async () => {
                const amount = parseFloat(amountInput.value);
                const currency = currencySelect.value;
                
                if (amount && currency) {
                    try {
                        const rate = await this.getExchangeRate(currency);
                        const xrpAmount = amount / rate;
                        
                        document.getElementById('xrp-amount').textContent = 
                            `≈ ${xrpAmount.toFixed(6)} XRP`;
                    } catch (error) {
                        console.error('Rate conversion error:', error);
                    }
                }
            };

            amountInput.addEventListener('input', updateRate);
            currencySelect.addEventListener('change', updateRate);
        }
    },

    async createPaymentRequest(form) {
        const formData = new FormData(form);
        const data = {
            amount: parseFloat(formData.get('amount')),
            currency: formData.get('currency'),
            description: formData.get('description'),
            expiry: parseInt(formData.get('expiry'))
        };

        try {
            const response = await ApiClient.post('/api/payments/request', data);
            
            if (response.status === 'success') {
                this.showQRCode(response.data);
                NotificationSystem.show('Payment request created successfully', 'success');
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('Payment request creation failed:', error);
            NotificationSystem.show(
                'Failed to create payment request',
                'error'
            );
        }
    },

    setupQRCodeGenerator() {
        const modal = document.getElementById('qr-modal');
        if (!modal) return;

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideQRCode();
            }
        });
    },

    showQRCode(paymentData) {
        const modal = document.getElementById('qr-modal');
        const qrImage = document.getElementById('qr-code');
        const paymentDetails = document.getElementById('payment-details');

        if (modal && qrImage && paymentDetails) {
            qrImage.src = paymentData.qr_code;
            paymentDetails.innerHTML = `
                <p class="text-lg font-semibold">${paymentData.amount} ${paymentData.currency}</p>
                <p class="text-sm text-gray-500">${paymentData.description || ''}</p>
                <p class="text-xs text-gray-400">Expires in ${this.formatExpiry(paymentData.expiry)}</p>
            `;

            modal.classList.remove('hidden');
            this.startExpiryCountdown(paymentData.expiry);
        }
    },

    hideQRCode() {
        const modal = document.getElementById('qr-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    },

    async getExchangeRate(currency) {
        try {
            const response = await ApiClient.get(`/api/rates/${currency}`);
            return response.rate;
        } catch (error) {
            console.error('Failed to fetch exchange rate:', error);
            throw error;
        }
    },

    formatExpiry(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    },

    startExpiryCountdown(expiryTime) {
        const countdownElement = document.getElementById('expiry-countdown');
        if (!countdownElement) return;

        const endTime = Date.now() + (expiryTime * 1000);
        
        const updateCountdown = () => {
            const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
            
            if (remaining === 0) {
                clearInterval(interval);
                this.hideQRCode();
                NotificationSystem.show('Payment request expired', 'warning');
            } else {
                countdownElement.textContent = this.formatExpiry(remaining);
            }
        };

        const interval = setInterval(updateCountdown, 1000);
        updateCountdown();
    },

    async initializePaymentHistory() {
        const historyTable = document.getElementById('payment-history');
        if (!historyTable) return;

        try {
            const response = await ApiClient.get('/api/payments/history');
            this.renderPaymentHistory(response.payments);
        } catch (error) {
            console.error('Failed to fetch payment history:', error);
            NotificationSystem.show(
                'Failed to load payment history',
                'error'
            );
        }
    },

    renderPaymentHistory(payments) {
        const tbody = document.querySelector('#payment-history tbody');
        if (!tbody) return;

        tbody.innerHTML = payments.map(payment => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${new Date(payment.timestamp).toLocaleString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${payment.amount} ${payment.currency}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${payment.description || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                        payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                    }">
                        ${payment.status}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="PaymentManager.showPaymentDetails('${payment.id}')"
                            class="text-indigo-600 hover:text-indigo-900">
                        Details
                    </button>
                </td>
            </tr>
        `).join('');
    },

    async showPaymentDetails(paymentId) {
        try {
            const response = await ApiClient.get(`/api/payments/${paymentId}`);
            
            // Show payment details in modal
            const modal = document.getElementById('payment-details-modal');
            if (modal) {
                modal.querySelector('.modal-content').innerHTML = this.formatPaymentDetails(response.payment);
                modal.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Failed to fetch payment details:', error);
            NotificationSystem.show(
                'Failed to load payment details',
                'error'
            );
        }
    },

    formatPaymentDetails(payment) {
        return `
            <div class="space-y-4">
                <div>
                    <h3 class="text-lg font-medium text-gray-900">Payment Details</h3>
                    <p class="mt-1 text-sm text-gray-500">
                        Transaction ID: ${payment.transaction_id}
                    </p>
                </div>

                <div class="border-t border-gray-200 pt-4">
                    <dl class="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Amount</dt>
                            <dd class="mt-1 text-sm text-gray-900">
                                ${payment.amount} ${payment.currency}
                            </dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Status</dt>
                            <dd class="mt-1 text-sm text-gray-900">
                                ${payment.status}
                            </dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Created</dt>
                            <dd class="mt-1 text-sm text-gray-900">
                                ${new Date(payment.created_at).toLocaleString()}
                            </dd>
                        </div>
                        <div>
                            <dt class="text-sm font-medium text-gray-500">Updated</dt>
                            <dd class="mt-1 text-sm text-gray-900">
                                ${new Date(payment.updated_at).toLocaleString()}
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>
        `;
    }
};

// Initialize payment functionality
document.addEventListener('DOMContentLoaded', () => {
    PaymentManager.initialize();
}); 