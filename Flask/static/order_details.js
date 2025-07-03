class Cart {
    constructor() {
        this.subtotal = 0;
        this.initializeSubtotal();
        this.initUrlParams();
        this.updateTotalCostField();
    }

    initializeSubtotal() {
        const prices = document.querySelectorAll('.current-price');
        prices.forEach(priceElem => {
            const priceValue = this.parsePrice(priceElem.innerHTML);
            this.subtotal += priceValue;
        });
        this.updateSubtotalDisplay();
    }

    parsePrice(priceString) {
        return parseFloat(priceString.replace('KSh ', '').replace(',', '')) || 0;
    }

    updateSubtotalDisplay() {
        const formattedSubtotal = this.subtotal.toFixed(2);
        document.getElementById('subtotal').innerHTML = formattedSubtotal;
        document.getElementById('subtotal1').innerHTML = formattedSubtotal;
    }

    updateSubtotal() {
        let total = 0;
        const prices = document.querySelectorAll('.current-price');
        prices.forEach(priceElem => {
            total += this.parsePrice(priceElem.innerHTML);
        });
        this.subtotal = total;
        this.updateSubtotalDisplay();
        this.updateTotalCostField();
    }

    updateTotalCostField() {
        document.getElementById('total_cost').value = this.subtotal.toFixed(2);
    }

    increment(productId, price) {
        const quantityElem = document.getElementById(`quantity-${productId}`);
        const priceElem = document.getElementById(`price-${productId}`);
        const hiddenQuantityElem = document.getElementById(`quantity-hidden-${productId}`);

        let currentQuantity = parseInt(quantityElem.innerHTML);
        let newQuantity = currentQuantity + 1;

        quantityElem.innerHTML = newQuantity;
        priceElem.innerHTML = `KSh ${(newQuantity * price).toFixed(2)}`;
        hiddenQuantityElem.value = newQuantity;

        this.updateSubtotal();
    }

    decrement(productId, price) {
        const quantityElem = document.getElementById(`quantity-${productId}`);
        const priceElem = document.getElementById(`price-${productId}`);
        const hiddenQuantityElem = document.getElementById(`quantity-hidden-${productId}`);

        let currentQuantity = parseInt(quantityElem.innerHTML);
        if (currentQuantity > 1) {
            let newQuantity = currentQuantity - 1;

            quantityElem.innerHTML = newQuantity;
            priceElem.innerHTML = `KSh ${(newQuantity * price).toFixed(2)}`;
            hiddenQuantityElem.value = newQuantity;

            this.updateSubtotal();
        }
    }

    getUrlParams() {
        const params = {};
        const parser = new URLSearchParams(window.location.search);

        for (let [key, value] of parser.entries()) {
            if (key === 'product_ids') {
                params['product_ids'] = value.split(',');
            } else {
                params[key] = value;
            }
        }

        return params;
    }

    initUrlParams() {
        const params = this.getUrlParams();

        if (params['product_ids']) {
            const productIds = params['product_ids'];
            document.getElementById('product_ids').value = productIds.join(',');

            productIds.forEach(productId => {
                const element = document.getElementById(`quantity-hidden-${productId}`);
                if (!element) {
                    console.error(`Element not found for productId: ${productId}`);
                } else {
                    element.value = 1;
                }
            });
        }
    }

    calculateTotalCost() {
        const totalCostElem = document.getElementById('subtotal1');
        const totalCost = this.parsePrice(totalCostElem.innerText.trim());
        return totalCost;
    }
}

// Initialize the cart on page load
window.onload = function () {
    const cart = new Cart();

    // Expose methods for increment and decrement
    window.increment = (productId, price) => cart.increment(productId, price);
    window.decrement = (productId, price) => cart.decrement(productId, price);
};
