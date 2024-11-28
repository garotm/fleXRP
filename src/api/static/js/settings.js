/**
 * Settings management functionality
 */

const SettingsManager = {
    initialize() {
        this.setupTabs();
        this.setupForms();
        this.setupAPIKeyManagement();
        this.setupWebhookTesting();
        this.loadCurrentSettings();
    },

    setupTabs() {
        const tabs = document.querySelectorAll('[data-tab]');
        const contents = document.querySelectorAll('[data-tab-content]');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active classes
                tabs.forEach(t => t.classList.remove('active-tab'));
                contents.forEach(c => c.classList.add('hidden'));

                // Add active class to clicked tab
                tab.classList.add('active-tab');
                
                // Show corresponding content
                const content = document.querySelector(
                    `[data-tab-content="${tab.dataset.tab}"]`
                );
                if (content) {
                    content.classList.remove('hidden');
                }
            });
        });
    },

    setupForms() {
        // General Settings Form
        const generalForm = document.getElementById('general-settings-form');
        if (generalForm) {
            generalForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveGeneralSettings(generalForm);
            });
        }

        // Security Settings Form
        const securityForm = document.getElementById('security-settings-form');
        if (securityForm) {
            securityForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveSecuritySettings(securityForm);
            });
        }

        // Notification Settings Form
        const notificationForm = document.getElementById('notification-settings-form');
        if (notificationForm) {
            notificationForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveNotificationSettings(notificationForm);
            });
        }
    },

    async loadCurrentSettings() {
        try {
            const response = await ApiClient.get('/api/settings');
            this.populateSettings(response.settings);
        } catch (error) {
            console.error('Failed to load settings:', error);
            NotificationSystem.show(
                'Failed to load current settings',
                'error'
            );
        }
    },

    populateSettings(settings) {
        // Populate general settings
        Object.entries(settings.general || {}).forEach(([key, value]) => {
            const input = document.querySelector(`[name="general.${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            }
        });

        // Populate security settings
        Object.entries(settings.security || {}).forEach(([key, value]) => {
            const input = document.querySelector(`[name="security.${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            }
        });

        // Populate notification settings
        Object.entries(settings.notifications || {}).forEach(([key, value]) => {
            const input = document.querySelector(`[name="notifications.${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else {
                    input.value = value;
                }
            }
        });
    },

    async saveGeneralSettings(form) {
        const formData = new FormData(form);
        const settings = {};

        formData.forEach((value, key) => {
            if (key.startsWith('general.')) {
                const settingKey = key.replace('general.', '');
                settings[settingKey] = value;
            }
        });

        try {
            await ApiClient.post('/api/settings/general', settings);
            NotificationSystem.show('General settings saved successfully', 'success');
        } catch (error) {
            console.error('Failed to save general settings:', error);
            NotificationSystem.show('Failed to save general settings', 'error');
        }
    },

    async saveSecuritySettings(form) {
        const formData = new FormData(form);
        const settings = {};

        formData.forEach((value, key) => {
            if (key.startsWith('security.')) {
                const settingKey = key.replace('security.', '');
                settings[settingKey] = value;
            }
        });

        try {
            await ApiClient.post('/api/settings/security', settings);
            NotificationSystem.show('Security settings saved successfully', 'success');
        } catch (error) {
            console.error('Failed to save security settings:', error);
            NotificationSystem.show('Failed to save security settings', 'error');
        }
    },

    setupAPIKeyManagement() {
        const generateButton = document.getElementById('generate-api-key');
        if (generateButton) {
            generateButton.addEventListener('click', async () => {
                try {
                    const response = await ApiClient.post('/api/settings/api-key');
                    this.showAPIKeyModal(response.key);
                } catch (error) {
                    console.error('Failed to generate API key:', error);
                    NotificationSystem.show('Failed to generate API key', 'error');
                }
            });
        }

        // Setup API key revocation
        const revokeButtons = document.querySelectorAll('[data-revoke-key]');
        revokeButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const keyId = button.dataset.revokeKey;
                if (await this.confirmRevocation(keyId)) {
                    await this.revokeAPIKey(keyId);
                }
            });
        });
    },

    async showAPIKeyModal(apiKey) {
        const modal = document.getElementById('api-key-modal');
        const keyDisplay = document.getElementById('api-key-display');
        
        if (modal && keyDisplay) {
            keyDisplay.textContent = apiKey;
            modal.classList.remove('hidden');

            // Setup copy button
            const copyButton = modal.querySelector('[data-copy]');
            if (copyButton) {
                copyButton.addEventListener('click', () => {
                    navigator.clipboard.writeText(apiKey);
                    NotificationSystem.show('API key copied to clipboard', 'success');
                });
            }
        }
    },

    async confirmRevocation(keyId) {
        return confirm(
            'Are you sure you want to revoke this API key? ' +
            'This action cannot be undone.'
        );
    },

    async revokeAPIKey(keyId) {
        try {
            await ApiClient.delete(`/api/settings/api-key/${keyId}`);
            NotificationSystem.show('API key revoked successfully', 'success');
            
            // Remove the key from the UI
            const keyElement = document.querySelector(`[data-key-id="${keyId}"]`);
            if (keyElement) {
                keyElement.remove();
            }
        } catch (error) {
            console.error('Failed to revoke API key:', error);
            NotificationSystem.show('Failed to revoke API key', 'error');
        }
    },

    setupWebhookTesting() {
        const testButton = document.getElementById('test-webhook');
        if (testButton) {
            testButton.addEventListener('click', async () => {
                const url = document.querySelector('[name="notifications.webhook_url"]').value;
                if (!url) {
                    NotificationSystem.show('Please enter a webhook URL first', 'warning');
                    return;
                }

                try {
                    const response = await ApiClient.post('/api/settings/test-webhook', { url });
                    NotificationSystem.show(
                        'Webhook test completed successfully',
                        'success'
                    );
                } catch (error) {
                    console.error('Webhook test failed:', error);
                    NotificationSystem.show(
                        'Webhook test failed. Please check the URL and try again',
                        'error'
                    );
                }
            });
        }
    }
};

// Initialize settings functionality
document.addEventListener('DOMContentLoaded', () => {
    SettingsManager.initialize();
}); 