
  // Function to add product ID to localStorage
function addToCart() {
    // Retrieve product IDs from localStorage
    const productIdInput = document.querySelector('.product-id');
    const productId = productIdInput.value;
    console.log("Product added to cart:", productId);
    let productIds = JSON.parse(localStorage.getItem('cart')) || [];

    // Check if the product is already in the cart
    if (!productIds.includes(productId)) {
        // Add the product ID to the array
        productIds.push(productId);
        // Save the updated array to localStorage
        localStorage.setItem('cart', JSON.stringify(productIds));
        // alert('Product ' + productId + ' added to cart.');
        const cartBadge = document.getElementById('cart-quantity-badge');
        cartBadge.style.display = 'inline'; // Show the badge
        location.reload();
    } else {
        alert('Product ' + productId + ' is already in the cart.');
    }
}
// Function to submit the cart form with product IDs from localStorage
function goToCart() {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    if (cart.length > 0) {
        let productIds = cart.join(',');  // Join all product IDs as comma-separated string
        document.getElementById('productIds').value = productIds;  // Set the product IDs to the hidden input
        document.getElementById('cartForm').submit();  // Submit the form
    } else {
        alert('No products in the cart.');
    }
}

let bigImg = document.querySelector('.big-img img');
function showImg(pic){
    bigImg.src = pic;
}
