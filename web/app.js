document.addEventListener("DOMContentLoaded", () => {
  fetchProducts();

  // Add event listener to the form
  // const form = document.querySelector("form");
  // form.addEventListener("submit", (event) => {
  //   event.preventDefault(); // Prevent default form submission behavior
  //   addProduct(); // Call the addProduct function
  // });

  // chat show/hide
  const button = document.getElementById("chat_button");
  const popup = document.getElementById("chat_popup");

  button.addEventListener("click", () => {
    if (popup.style.display === "none" || popup.style.display === "") {
      popup.style.display = "block";
    } else {
      popup.style.display = "none";
    }
  });

  // send message
  const sendButton = document.getElementById("send_message_btn");

  sendButton.addEventListener("click", () => {
    sendMessage();
  });
});

//_______________________functions_____________________________

function sendMessage() {
  const message = document.getElementById("chat_input").value;
  const messages = document.getElementById("message_container");
  const popup = document.getElementById("chat_popup");
  const loader = document.getElementById("loader");

  if (message === "") {
    console.log("No message to send.");
    return;
  } else {
    try {
      const user = document.createElement("p");
      user.textContent = message;
      user.className = "user";
      messages.appendChild(user);
      popup.scrollTo({
        top: popup.scrollHeight,
        behavior: "smooth",
      });

      loader.style.display = "block";

      fetch("http://localhost:5001/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Success:", data);
          const ai = document.createElement("p");
          
          ai.textContent = data.response;
          ai.className = "ai";

          messages.appendChild(ai);
          popup.scrollTo({
            top: popup.scrollHeight,
            behavior: "smooth",
          });
          loader.style.display = "none";
        });
    } catch (error) {
      console.error("Error sending message:", error);
      loader.style.display = "none";
    }
    console.log("Message sent: ", message);
    document.getElementById("chat_input").value = "";
  }
}

function fetchProducts() {
  fetch("http://127.0.0.1:5000/products")
    .then((response) => response.json())
    .then((data) => {
      displayProducts(data.products);
      console.log(data.products);
    })
    .catch((error) => {
      console.error("Error fetching products:", error);
    });
}

async function addProduct() {
  const productName = document.getElementById("product-name").value;
  const productDescription = document.getElementById(
    "product-description"
  ).value;
  const productPrice = document.getElementById("product-price").value;
  const productStock = document.getElementById("product-stock").value;
  const imageUrl = document.getElementById("product-image").value;

  const product = {
    name: productName,
    description: productDescription,
    price: parseFloat(productPrice),
    stock_items: parseInt(productStock, 10),
    url: imageUrl,
  };

  try {
    const response = await fetch("http://127.0.0.1:5000/add_new_products", {
      // Ensure this URL matches your Flask endpoint
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(product),
    });

    const data = await response.json();
    console.log("Success:", data);
    fetchProducts(); // Refresh the product list
  } catch (error) {
    console.error("Error adding product:", error);
  }
}

function displayProducts(products) {
  const productList = document.getElementById("product-list");
  productList.innerHTML = "";

  products.forEach((product) => {
    const productCard = document.createElement("div");
    productCard.className = "product-card";

    const productDetails = document.createElement("div");
    productDetails.className = "product-details";

    const productName = document.createElement("div");
    productName.className = "product-name";
    productName.textContent = product.name;

    const productImage = document.createElement("img");
    productImage.src = product.image_url;
    productImage.alt = product.name;
    productImage.className = "product_image";

    const productDescription = document.createElement("div");
    productDescription.className = "product-description";
    productDescription.textContent = product.description;

    const productPrice = document.createElement("div");
    productPrice.className = "product-price";
    productPrice.textContent = `Rs.${product.price.toFixed(2)}`;

    const productStock = document.createElement("div");
    productStock.className =
      product.stock_items > 0 ? "product-stock-true" : "product-stock-false";
    productStock.textContent = `In Stock: ${product.stock_items}`;

    productCard.appendChild(productImage);
    productDetails.appendChild(productName);
    productDetails.appendChild(productDescription);
    productDetails.appendChild(productPrice);
    productDetails.appendChild(productStock);

    productCard.appendChild(productDetails);

    productList.appendChild(productCard);
  });
}
