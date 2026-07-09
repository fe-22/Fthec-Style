const API_BASE = "";

const state = {
  products: [],
  filteredProducts: [],
  cart: [],
};

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const selectors = {
  productGrid: document.querySelector("#productGrid"),
  categorySelect: document.querySelector("#categorySelect"),
  searchInput: document.querySelector("#searchInput"),
  budgetInput: document.querySelector("#budgetInput"),
  cartCount: document.querySelector("#cartCount"),
  cartDrawer: document.querySelector("#cartDrawer"),
  openCartButton: document.querySelector("#openCartButton"),
  closeCartButton: document.querySelector("#closeCartButton"),
  cartBackdrop: document.querySelector("#cartBackdrop"),
  cartItems: document.querySelector("#cartItems"),
  cartTotal: document.querySelector("#cartTotal"),
  checkoutForm: document.querySelector("#checkoutForm"),
  checkoutResult: document.querySelector("#checkoutResult"),
  stylistForm: document.querySelector("#stylistForm"),
  stylistResult: document.querySelector("#stylistResult"),
};

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function splitTerms(value) {
  return String(value || "")
    .split(",")
    .map((item) => normalize(item))
    .filter(Boolean);
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }

  return response.json();
}

async function loadProducts() {
  selectors.productGrid.innerHTML = `<div class="empty-state">Carregando pecas...</div>`;

  try {
    state.products = await request("/api/v1/products?active_only=true&in_stock_only=true");
    state.filteredProducts = state.products;
    hydrateCategories();
    renderProducts();
  } catch (error) {
    selectors.productGrid.innerHTML = `
      <div class="error-state">
        Nao consegui carregar o catalogo. Confirme se o backend esta rodando na porta 8000.
      </div>
    `;
  }
}

function hydrateCategories() {
  const categories = [...new Set(state.products.map((product) => product.category))].sort();
  selectors.categorySelect.innerHTML = `<option value="">Todas</option>`;

  for (const category of categories) {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    selectors.categorySelect.append(option);
  }
}

function applyFilters() {
  const search = normalize(selectors.searchInput.value);
  const category = selectors.categorySelect.value;
  const budget = Number(selectors.budgetInput.value || 0);

  state.filteredProducts = state.products.filter((product) => {
    const haystack = normalize(
      [
        product.name,
        product.description,
        product.category,
        ...(product.tags || []),
        ...(product.style_keywords || []),
        ...(product.colors || []),
      ].join(" ")
    );

    const matchesSearch = !search || haystack.includes(search);
    const matchesCategory = !category || product.category === category;
    const matchesBudget = !budget || Number(product.price) <= budget;
    return matchesSearch && matchesCategory && matchesBudget;
  });

  renderProducts();
}

function renderProducts() {
  const template = document.querySelector("#productCardTemplate");
  selectors.productGrid.innerHTML = "";

  if (!state.filteredProducts.length) {
    selectors.productGrid.innerHTML = `
      <div class="empty-state">
        Nenhuma peca encontrada com esses filtros. Tente ampliar o orcamento ou mudar a busca.
      </div>
    `;
    return;
  }

  state.filteredProducts.forEach((product, index) => {
    const card = template.content.firstElementChild.cloneNode(true);
    card.style.animationDelay = `${index * 55}ms`;
    const productArt = card.querySelector(".product-art");
    if (product.image_url) {
      productArt.classList.add("has-image");
      const image = document.createElement("img");
      image.src = product.image_url;
      image.alt = product.name;
      productArt.prepend(image);
    }
    card.querySelector(".product-category").textContent = product.category;
    card.querySelector("h3").textContent = product.name;
    card.querySelector(".product-description").textContent = product.description;
    card.querySelector(".product-price").textContent = currency.format(Number(product.price));
    card.querySelector(".product-stock").textContent = `${product.stock} em estoque`;

    const tags = card.querySelector(".product-tags");
    [...(product.tags || []), ...(product.colors || []).slice(0, 2)]
      .slice(0, 5)
      .forEach((tag) => {
        const chip = document.createElement("span");
        chip.textContent = tag;
        tags.append(chip);
      });

    card.querySelector(".add-button").addEventListener("click", () => addToCart(product));
    selectors.productGrid.append(card);
  });
}

function addToCart(product) {
  const existing = state.cart.find((item) => item.product.id === product.id);

  if (existing) {
    existing.quantity += 1;
  } else {
    state.cart.push({
      product,
      quantity: 1,
      size: product.sizes?.[0] || null,
      color: product.colors?.[0] || null,
    });
  }

  renderCart();
  openCart();
}

function removeFromCart(productId) {
  state.cart = state.cart.filter((item) => item.product.id !== productId);
  renderCart();
}

function renderCart() {
  const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const total = state.cart.reduce(
    (sum, item) => sum + Number(item.product.price) * item.quantity,
    0
  );

  selectors.cartCount.textContent = totalQuantity;
  selectors.cartTotal.textContent = currency.format(total);
  selectors.cartItems.innerHTML = "";
  selectors.checkoutResult.innerHTML = "";

  if (!state.cart.length) {
    selectors.cartItems.innerHTML = `<div class="empty-state">Sua sacola esta vazia.</div>`;
    return;
  }

  for (const item of state.cart) {
    const row = document.createElement("article");
    row.className = "cart-item";
    row.innerHTML = `
      <div>
        <strong>${item.product.name}</strong>
        <span>${item.quantity}x ${currency.format(Number(item.product.price))}</span>
        <span>${[item.size && `tam. ${item.size}`, item.color && `cor ${item.color}`]
          .filter(Boolean)
          .join(" · ")}</span>
      </div>
      <button type="button" aria-label="Remover ${item.product.name}">Remover</button>
    `;
    row.querySelector("button").addEventListener("click", () => removeFromCart(item.product.id));
    selectors.cartItems.append(row);
  }
}

function openCart() {
  selectors.cartDrawer.setAttribute("aria-hidden", "false");
}

function closeCart() {
  selectors.cartDrawer.setAttribute("aria-hidden", "true");
}

async function checkout(event) {
  event.preventDefault();

  if (!state.cart.length) {
    selectors.checkoutResult.textContent = "Adicione pelo menos uma peca para gerar atendimento.";
    return;
  }

  const payload = {
    customer: {
      name: document.querySelector("#customerName").value,
      phone: document.querySelector("#customerPhone").value,
      email: null,
      style_notes: "",
    },
    items: state.cart.map((item) => ({
      product_id: item.product.id,
      quantity: item.quantity,
      size: item.size,
      color: item.color,
    })),
    notes: document.querySelector("#checkoutNotes").value,
  };

  selectors.checkoutResult.textContent = "Gerando mensagem para a consultora...";

  try {
    const result = await request("/api/v1/whatsapp/checkout", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (result.wa_me_url) {
      selectors.checkoutResult.innerHTML = `
        Atendimento criado para o pedido #${result.order.id}.
        <a href="${result.wa_me_url}" target="_blank" rel="noreferrer">Enviar mensagem no WhatsApp</a>
      `;
      window.open(result.wa_me_url, "_blank", "noopener,noreferrer");
      return;
    }

    selectors.checkoutResult.innerHTML = `
      <p>Atendimento criado para o pedido #${result.order.id}. Configure o numero da consultora no .env para gerar o link automatico.</p>
      <div class="message-box">${result.message}</div>
    `;
  } catch (error) {
    selectors.checkoutResult.textContent = "Nao foi possivel gerar o checkout. Revise os dados e tente novamente.";
  }
}

function inferProfileFromText(message) {
  const text = normalize(message);
  const profile = {
    occasion: document.querySelector("#occasionInput").value || null,
    style_preferences: splitTerms(document.querySelector("#styleInput").value),
    preferred_colors: splitTerms(document.querySelector("#colorInput").value),
    sizes: splitTerms(document.querySelector("#sizeInput").value),
    avoid: [],
  };

  const occasions = ["trabalho", "festa", "jantar", "casual", "viagem", "verao"];
  const colors = ["preto", "branco", "off white", "bege", "areia", "verde", "terracota"];
  const styles = ["elegante", "minimalista", "romantico", "classico", "moderno", "despojado"];
  const sizes = ["pp", "p", "m", "g", "gg", "36", "38", "40", "42", "44"];

  if (!profile.occasion) {
    profile.occasion = occasions.find((term) => text.includes(term)) || null;
  }

  for (const color of colors) {
    if (text.includes(color) && !profile.preferred_colors.includes(color)) {
      profile.preferred_colors.push(color);
    }
  }

  for (const style of styles) {
    if (text.includes(style) && !profile.style_preferences.includes(style)) {
      profile.style_preferences.push(style);
    }
  }

  for (const size of sizes) {
    const pattern = new RegExp(`(^|\\s)${size}(\\s|$)`, "i");
    if (pattern.test(text) && !profile.sizes.includes(size)) {
      profile.sizes.push(size);
    }
  }

  const budgetMatch = text.match(/(?:r\$|ate|até)\s?(\d{2,5})/i);
  if (budgetMatch) {
    profile.max_budget = budgetMatch[1];
  }

  return profile;
}

async function askStylist(event) {
  event.preventDefault();

  const message = document.querySelector("#stylistMessage").value;
  const profile = inferProfileFromText(message);

  selectors.stylistResult.innerHTML = `<div class="stylist-response">Pensando em combinacoes...</div>`;

  try {
    const result = await request("/api/v1/stylist/chat", {
      method: "POST",
      body: JSON.stringify({ message, profile, limit: 3 }),
    });

    const cards = result.recommendations
      .map(
        (item) => `
          <article class="mini-rec">
            <strong>${item.product.name}</strong>
            <span>${currency.format(Number(item.product.price))}</span>
            <p>${item.reasons.slice(0, 2).join("; ")}</p>
          </article>
        `
      )
      .join("");

    selectors.stylistResult.innerHTML = `
      <div class="stylist-response">
        ${result.reply}
        <div class="mini-recs">${cards}</div>
      </div>
    `;
  } catch (error) {
    selectors.stylistResult.innerHTML = `
      <div class="stylist-response">Nao consegui consultar a stylist agora. Tente novamente em alguns segundos.</div>
    `;
  }
}

selectors.searchInput.addEventListener("input", applyFilters);
selectors.categorySelect.addEventListener("change", applyFilters);
selectors.budgetInput.addEventListener("input", applyFilters);
selectors.openCartButton.addEventListener("click", openCart);
selectors.closeCartButton.addEventListener("click", closeCart);
selectors.cartBackdrop.addEventListener("click", closeCart);
selectors.checkoutForm.addEventListener("submit", checkout);
selectors.stylistForm.addEventListener("submit", askStylist);

loadProducts();
renderCart();
