/* ============================================================
   Fthec Style — JavaScript
   ============================================================ */

'use strict';

// ---------- Catálogo de produtos ----------
const products = [
  {
    id: 1,
    name: 'Camiseta Básica Branca',
    category: 'roupas',
    price: 79.90,
    emoji: '👕',
  },
  {
    id: 2,
    name: 'Calça Jeans Skinny',
    category: 'roupas',
    price: 189.90,
    emoji: '👖',
  },
  {
    id: 3,
    name: 'Vestido Floral',
    category: 'roupas',
    price: 149.90,
    emoji: '👗',
  },
  {
    id: 4,
    name: 'Moletom Oversized',
    category: 'roupas',
    price: 169.90,
    emoji: '🧥',
  },
  {
    id: 5,
    name: 'Tênis Casual Branco',
    category: 'calcados',
    price: 259.90,
    emoji: '👟',
  },
  {
    id: 6,
    name: 'Sandália Rasteira',
    category: 'calcados',
    price: 119.90,
    emoji: '🩴',
  },
  {
    id: 7,
    name: 'Bota Cano Curto',
    category: 'calcados',
    price: 319.90,
    emoji: '👢',
  },
  {
    id: 8,
    name: 'Bolsa Transversal',
    category: 'acessorios',
    price: 199.90,
    emoji: '👜',
  },
  {
    id: 9,
    name: 'Óculos de Sol',
    category: 'acessorios',
    price: 129.90,
    emoji: '🕶️',
  },
  {
    id: 10,
    name: 'Relógio Minimalista',
    category: 'acessorios',
    price: 349.90,
    emoji: '⌚',
  },
  {
    id: 11,
    name: 'Colar Dourado',
    category: 'acessorios',
    price: 89.90,
    emoji: '📿',
  },
  {
    id: 12,
    name: 'Jaqueta Jeans',
    category: 'roupas',
    price: 229.90,
    emoji: '🧥',
  },
];

// ---------- Estado do carrinho ----------
let cart = [];

// ---------- Renderizar produtos ----------
function formatPrice(value) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function renderProducts(filter = 'all') {
  const grid = document.getElementById('productGrid');
  grid.innerHTML = '';

  const filtered = filter === 'all'
    ? products
    : products.filter((p) => p.category === filter);

  filtered.forEach((product) => {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.dataset.category = product.category;

    card.innerHTML = `
      <div class="product-card__image-placeholder" aria-hidden="true">
        <span>${product.emoji}</span>
      </div>
      <div class="product-card__body">
        <p class="product-card__category">${categoryLabel(product.category)}</p>
        <h3 class="product-card__name">${product.name}</h3>
        <p class="product-card__price">${formatPrice(product.price)}</p>
        <button
          class="product-card__add"
          data-id="${product.id}"
          aria-label="Adicionar ${product.name} ao carrinho"
        >
          Adicionar ao carrinho
        </button>
      </div>
    `;

    grid.appendChild(card);
  });

  // Attach add-to-cart listeners
  grid.querySelectorAll('.product-card__add').forEach((btn) => {
    btn.addEventListener('click', () => addToCart(Number(btn.dataset.id)));
  });
}

function categoryLabel(cat) {
  const labels = { roupas: 'Roupas', acessorios: 'Acessórios', calcados: 'Calçados' };
  return labels[cat] || cat;
}

// ---------- Filtros ----------
document.querySelectorAll('.filter-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    renderProducts(btn.dataset.filter);
  });
});

// ---------- Carrinho ----------
function addToCart(productId) {
  const product = products.find((p) => p.id === productId);
  if (!product) return;

  const existing = cart.find((item) => item.id === productId);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1 });
  }

  updateCartUI();
  openCart();
}

function removeFromCart(productId) {
  cart = cart.filter((item) => item.id !== productId);
  updateCartUI();
}

function updateCartUI() {
  const count = cart.reduce((sum, item) => sum + item.qty, 0);
  const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);

  document.getElementById('cartCount').textContent = count;
  document.getElementById('cartTotal').textContent = formatPrice(total);

  const listEl = document.getElementById('cartItems');
  listEl.innerHTML = '';

  if (cart.length === 0) {
    listEl.innerHTML = '<p class="empty-cart">Seu carrinho está vazio.</p>';
    return;
  }

  cart.forEach((item) => {
    const li = document.createElement('li');
    li.className = 'cart-item';
    li.innerHTML = `
      <span class="cart-item__emoji">${item.emoji}</span>
      <div class="cart-item__info">
        <p>${item.name}</p>
        <small>${item.qty}x ${formatPrice(item.price)}</small>
      </div>
      <button class="cart-item__remove" data-id="${item.id}" aria-label="Remover ${item.name}">✕</button>
    `;
    listEl.appendChild(li);
  });

  listEl.querySelectorAll('.cart-item__remove').forEach((btn) => {
    btn.addEventListener('click', () => removeFromCart(Number(btn.dataset.id)));
  });
}

// ---------- Abrir / fechar carrinho ----------
function openCart() {
  document.getElementById('cartDrawer').classList.add('open');
  document.getElementById('cartOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeCart() {
  document.getElementById('cartDrawer').classList.remove('open');
  document.getElementById('cartOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('cartBtn').addEventListener('click', openCart);
document.getElementById('cartClose').addEventListener('click', closeCart);
document.getElementById('cartOverlay').addEventListener('click', closeCart);

// ---------- Formulário de contato ----------
document.getElementById('contactForm').addEventListener('submit', (e) => {
  e.preventDefault();
  alert('Mensagem enviada! Entraremos em contato em breve. 😊');
  e.target.reset();
});

// ---------- Init ----------
renderProducts();
updateCartUI();
