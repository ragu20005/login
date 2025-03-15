class EcommerceAnalysis {
    constructor() {
        this.priceChart = null;
        this.init();
    }

    init() {
        this.initCharts();
        this.loadTrackedProducts();
        this.loadCompetitorData();
        this.loadMarketInsights();
        this.setupEventListeners();
    }

    initCharts() {
        const ctx = document.getElementById('priceHistoryChart').getContext('2d');
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price History Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Price ($)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }

    async loadTrackedProducts() {
        try {
            const response = await fetch('/api/ecommerce/tracked-products');
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
                <div class="product-info">
                    <h4>${product.name}</h4>
                    <p class="price">Current Price: $${product.current_price}</p>
                    <p class="price-change ${product.price_change >= 0 ? 'positive' : 'negative'}">
                        ${product.price_change}% from last week
                    </p>
                </div>
                <div class="product-actions">
                    <button onclick="ecommerce.viewProductDetails(${product.id})">
                        Details
                    </button>
                    <button onclick="ecommerce.viewCompetitors(${product.id})">
                        Competitors
                    </button>
                </div>
            </div>
        `).join('');
    }

    async loadCompetitorData() {
        try {
            const response = await fetch('/api/ecommerce/competitor-analysis');
            const data = await response.json();
            this.displayCompetitorData(data);
        } catch (error) {
            this.showError('Failed to load competitor data');
        }
    }

    async loadMarketInsights() {
        try {
            const response = await fetch('/api/ecommerce/market-insights');
            const data = await response.json();
            this.displayMarketInsights(data);
        } catch (error) {
            this.showError('Failed to load market insights');
        }
    }

    setupEventListeners() {
        document.getElementById('addProductForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAddProduct(e);
        });
    }

    showError(message) {
        // Implement error notification system
        console.error(message);
    }

    showSuccess(message) {
        // Implement success notification system
        console.log(message);
    }
}

// Initialize
const ecommerce = new EcommerceAnalysis();