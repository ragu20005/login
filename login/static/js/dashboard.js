class Dashboard {
    constructor() {
        this.priceChart = null;
        this.init();
    }

    init() {
        this.loadTrackedProducts();
        this.loadRecentActivities('searches'); // Default tab
        
        // Initialize Chart.js
        const ctx = document.getElementById('priceHistoryChart').getContext('2d');
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    async loadTrackedProducts() {
        try {
            const response = await fetch('/api/tracked-products');
            const data = await response.json();
            this.displayTrackedProducts(data.products);
        } catch (error) {
            this.showError('Failed to load tracked products');
        }
    }

    displayTrackedProducts(products) {
        const container = document.getElementById('trackedProductsList');
        container.innerHTML = products.map(product => `
            <div class="product-card">
                <h4>${product.name}</h4>
                <p>Current Price: $${product.current_price}</p>
                <p>Target Price: $${product.target_price}</p>
                <div class="actions">
                    <button onclick="dashboard.viewPriceHistory(${product.id})">
                        Price History
                    </button>
                    <button onclick="dashboard.viewCompetitors(${product.id})">
                        Competitors
                    </button>
                    <button onclick="dashboard.findSimilarProducts('${product.name}')">
                        Similar
                    </button>
                </div>
            </div>
        `).join('');
    }

    async viewPriceHistory(productId) {
        try {
            const response = await fetch(`/api/price-history/${productId}`);
            const data = await response.json();
            this.updatePriceChart(data.history);
        } catch (error) {
            this.showError('Failed to load price history');
        }
    }

    updatePriceChart(history) {
        const labels = history.map(h => h.date);
        const prices = history.map(h => h.price);

        this.priceChart.data.labels = labels;
        this.priceChart.data.datasets = [{
            label: 'Price History',
            data: prices,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }];
        this.priceChart.update();
    }

    async loadRecentActivities(tab) {
        const container = document.getElementById('activityContent');
        container.innerHTML = '<div class="loading">Loading...</div>';

        try {
            let endpoint;
            switch(tab) {
                case 'searches':
                    endpoint = '/api/recent-searches';
                    break;
                case 'price-alerts':
                    endpoint = '/api/price-alerts';
                    break;
                case 'competitors':
                    endpoint = '/api/competitor-updates';
                    break;
            }

            const response = await fetch(endpoint);
            const data = await response.json();
            this.displayActivities(data, tab);
        } catch (error) {
            this.showError(`Failed to load ${tab}`);
        }
    }

    displayActivities(data, tab) {
        const container = document.getElementById('activityContent');
        let html = '';

        switch(tab) {
            case 'searches':
                html = this.renderSearchActivities(data);
                break;
            case 'price-alerts':
                html = this.renderPriceAlerts(data);
                break;
            case 'competitors':
                html = this.renderCompetitorUpdates(data);
                break;
        }

        container.innerHTML = html;
    }

    async handleAddProduct(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/api/track-product', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(Object.fromEntries(formData))
            });
            
            if (response.ok) {
                this.showSuccess('Product added successfully');
                this.loadTrackedProducts();
                closeProductTrackingModal();
                form.reset();
            } else {
                const data = await response.json();
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Failed to add product');
        }
    }

    showError(message) {
        // Implement error notification
        console.error(message);
    }

    showSuccess(message) {
        // Implement success notification
        console.log(message);
    }
}

// Modal functions
function showProductTrackingModal() {
    document.getElementById('productTrackingModal').style.display = 'block';
}

function closeProductTrackingModal() {
    document.getElementById('productTrackingModal').style.display = 'none';
}

function switchActivityTab(tab) {
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Load content
    dashboard.loadRecentActivities(tab);
}

// Initialize dashboard
const dashboard = new Dashboard();

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('productTrackingModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}