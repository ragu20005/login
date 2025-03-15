class ProductResearch {
    constructor() {
        this.init();
    }

    init() {
        // Initial load of tracked products
        this.loadTrackedProducts();
        
        // Add event listeners
        document.getElementById('addProductForm')
            .addEventListener('submit', this.handleAddProduct.bind(this));
    }

    async loadTrackedProducts() {
        try {
            const response = await fetch('/api/tracked-products');
            const data = await response.json();
            this.displayProducts(data.products);
        } catch (error) {
            this.showError('Failed to load products');
        }
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
                form.reset();
            } else {
                const data = await response.json();
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Failed to add product');
        }
    }

    async viewPriceHistory(productId) {
        try {
            const response = await fetch(`/api/price-history/${productId}`);
            const data = await response.json();
            this.displayPriceChart(data.history);
        } catch (error) {
            this.showError('Failed to load price history');
        }
    }

    async viewCompetitors(productId) {
        try {
            const response = await fetch(`/api/competitor-analysis/${productId}`);
            const data = await response.json();
            this.displayCompetitors(data.competitors);
        } catch (error) {
            this.showError('Failed to load competitors');
        }
    }

    async findSimilarProducts(productName) {
        try {
            const response = await fetch('/api/similar-products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ product_name: productName })
            });
            const data = await response.json();
            this.displaySimilarProducts(data);
        } catch (error) {
            this.showError('Failed to find similar products');
        }
    }

    // UI Helper Methods
    displayProducts(products) {
        const container = document.getElementById('tracked-products-list');
        container.innerHTML = products.map(product => `
            <div class="product-card">
                <h4>${product.name}</h4>
                <p>Current Price: $${product.current_price}</p>
                <p>Target Price: $${product.target_price}</p>
                <div class="actions">
                    <button onclick="productResearch.viewPriceHistory(${product.id})">
                        Price History
                    </button>
                    <button onclick="productResearch.viewCompetitors(${product.id})">
                        View Competitors
                    </button>
                    <button onclick="productResearch.findSimilarProducts('${product.name}')">
                        Similar Products
                    </button>
                </div>
            </div>
        `).join('');
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

// Initialize
const productResearch = new ProductResearch();