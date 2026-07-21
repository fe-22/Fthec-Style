const productForm = document.querySelector("#productForm");
const imageInput = document.querySelector("#imageInput");
const imagePreview = document.querySelector("#imagePreview");
const formStatus = document.querySelector("#formStatus");
const productList = document.querySelector("#adminProductList");
const formTitle = document.querySelector("#formTitle");
const formSubmitButton = document.querySelector("#formSubmitButton");
const cancelEditButton = document.querySelector("#cancelEditButton");
const erpReportForm = document.querySelector("#erpReportForm");
const erpReportInput = document.querySelector("#erpReportInput");
const erpReportSubmitButton = document.querySelector("#erpReportSubmitButton");
const erpReportStatus = document.querySelector("#erpReportStatus");

const fields = {
  sku: document.querySelector("#skuInput"),
  name: document.querySelector("#nameInput"),
  description: document.querySelector("#descriptionInput"),
  category: document.querySelector("#categoryInput"),
  purchasePrice: document.querySelector("#purchasePriceInput"),
  price: document.querySelector("#priceInput"),
  stock: document.querySelector("#stockInput"),
  sizes: document.querySelector("#sizesInput"),
  colors: document.querySelector("#colorsInput"),
  tags: document.querySelector("#tagsInput"),
  style: document.querySelector("#styleInput"),
};

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

let products = [];
let editingProduct = null;

function toList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function fromList(value) {
  return Array.isArray(value) ? value.join(", ") : "";
}

function slug(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .toUpperCase();
}

function setStatus(message, state = "neutral") {
  formStatus.textContent = message;
  formStatus.dataset.state = state;
}

function setErpReportStatus(message, state = "neutral") {
  erpReportStatus.textContent = message;
  erpReportStatus.dataset.state = state;
}

function setLoadingState(isLoading) {
  formSubmitButton.disabled = isLoading;
  cancelEditButton.disabled = isLoading;
}

async function api(path, options = {}) {
  const headers = {
    ...(options.body && !(options.body instanceof Blob) ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    let message = "";

    if (contentType.includes("application/json")) {
      const data = await response.json();
      message = Array.isArray(data.detail)
        ? data.detail.map((item) => item.msg).join(" ")
        : data.detail || data.message || "";
    } else {
      message = await response.text();
    }

    const error = new Error(message || `Erro HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function makeStateMessage(message, className = "empty-state") {
  const element = document.createElement("div");
  element.className = className;
  element.textContent = message;
  return element;
}

function renderImage(product) {
  if (!product.image_url) {
    const placeholder = document.createElement("div");
    placeholder.className = "admin-product-placeholder";
    return placeholder;
  }

  const image = document.createElement("img");
  image.src = product.image_url;
  image.alt = product.name;
  image.loading = "lazy";
  return image;
}

function renderProduct(product) {
  const row = document.createElement("article");
  row.className = "admin-product-row";
  if (!product.active) {
    row.classList.add("is-inactive");
  }

  const details = document.createElement("div");
  details.className = "admin-product-info";

  const titleLine = document.createElement("div");
  titleLine.className = "admin-product-title";

  const name = document.createElement("strong");
  name.textContent = product.name;

  const badge = document.createElement("span");
  badge.className = `status-badge ${product.active ? "is-active" : "is-hidden"}`;
  badge.textContent = product.active ? "Ativo" : "Oculto";

  titleLine.append(name, badge);

  const meta = document.createElement("small");
  meta.textContent = `${product.category} - ${product.sku}`;

  const stock = document.createElement("small");
  const purchasePrice = product.purchase_price
    ? `Compra ${money.format(Number(product.purchase_price))} - `
    : "";
  stock.textContent = `${purchasePrice}Venda ${money.format(Number(product.price))} - Estoque ${product.stock}`;

  details.append(titleLine, meta, stock);

  const actions = document.createElement("div");
  actions.className = "admin-row-actions";

  const editButton = document.createElement("button");
  editButton.className = "secondary-link small-button";
  editButton.type = "button";
  editButton.dataset.action = "edit";
  editButton.dataset.productId = String(product.id);
  editButton.textContent = "Editar";

  const toggleButton = document.createElement("button");
  toggleButton.className = "ghost-link small-button";
  toggleButton.type = "button";
  toggleButton.dataset.action = "toggle-active";
  toggleButton.dataset.productId = String(product.id);
  toggleButton.textContent = product.active ? "Ocultar" : "Ativar";

  actions.append(editButton, toggleButton);
  row.append(renderImage(product), details, actions);
  return row;
}

function renderProducts() {
  productList.replaceChildren();

  if (!products.length) {
    productList.append(makeStateMessage("Nenhum produto cadastrado ainda."));
    return;
  }

  const fragment = document.createDocumentFragment();
  products.forEach((product) => fragment.append(renderProduct(product)));
  productList.append(fragment);
}

async function loadProducts() {
  productList.replaceChildren(makeStateMessage("Carregando produtos..."));

  try {
    products = await api("/api/v1/products/admin?active_only=false");
    renderProducts();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "/admin";
      return;
    }

    productList.replaceChildren(makeStateMessage("Nao consegui carregar os produtos.", "error-state"));
  }
}

async function uploadImage(file) {
  if (!file) {
    return "";
  }

  const result = await api(
    `/api/v1/uploads/products?filename=${encodeURIComponent(file.name)}`,
    {
      method: "POST",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
    }
  );
  return result.image_url;
}

async function uploadErpReport(file) {
  const result = await api(
    `/api/v1/uploads/erp-report?filename=${encodeURIComponent(file.name)}`,
    {
      method: "POST",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
    }
  );
  return result;
}

function showPreview(url, altText = "Foto do produto") {
  imagePreview.replaceChildren();

  if (!url) {
    const empty = document.createElement("span");
    empty.textContent = "Escolha uma foto da peca";
    imagePreview.append(empty);
    return;
  }

  const image = document.createElement("img");
  image.src = url;
  image.alt = altText;
  imagePreview.append(image);
}

function setFormMode(product = null) {
  editingProduct = product;
  fields.sku.disabled = Boolean(product);
  formTitle.textContent = product ? "Editar produto" : "Novo produto";
  formSubmitButton.textContent = product ? "Salvar alteracoes" : "Cadastrar produto";
  cancelEditButton.hidden = !product;
}

function resetForm({ keepStatus = false } = {}) {
  productForm.reset();
  fields.stock.value = "1";
  setFormMode(null);
  showPreview("");

  if (!keepStatus) {
    setStatus("");
  }
}

function fillForm(product) {
  setFormMode(product);
  fields.sku.value = product.sku;
  fields.name.value = product.name;
  fields.description.value = product.description || "";
  fields.category.value = product.category;
  fields.purchasePrice.value = product.purchase_price || "";
  fields.price.value = product.price;
  fields.stock.value = product.stock;
  fields.sizes.value = fromList(product.sizes);
  fields.colors.value = fromList(product.colors);
  fields.tags.value = fromList(product.tags);
  fields.style.value = fromList(product.style_keywords);
  imageInput.value = "";
  showPreview(product.image_url, product.name);
  setStatus("Editando produto cadastrado.");
  productForm.scrollIntoView({ behavior: "smooth", block: "start" });
}

function buildPayload(imageUrl) {
  const payload = {
    name: fields.name.value.trim(),
    description: fields.description.value.trim(),
    category: fields.category.value.trim().toLowerCase(),
    purchase_price: fields.purchasePrice.value || null,
    price: fields.price.value,
    stock: Number(fields.stock.value),
    image_url: imageUrl || editingProduct?.image_url || null,
    sizes: toList(fields.sizes.value),
    colors: toList(fields.colors.value),
    tags: toList(fields.tags.value),
    style_keywords: toList(fields.style.value),
    active: editingProduct?.active ?? true,
  };

  if (!editingProduct) {
    payload.sku = fields.sku.value.trim();
  }

  return payload;
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files?.[0];
  if (!file) {
    showPreview(editingProduct?.image_url || "", editingProduct?.name || "Foto do produto");
    return;
  }

  const previewUrl = URL.createObjectURL(file);
  showPreview(previewUrl, "Previa da foto selecionada");
  imagePreview.querySelector("img")?.addEventListener("load", () => URL.revokeObjectURL(previewUrl), {
    once: true,
  });
});

fields.name.addEventListener("blur", (event) => {
  if (!editingProduct && !fields.sku.value.trim()) {
    fields.sku.value = `PRI-${slug(event.target.value)}`;
  }
});

cancelEditButton.addEventListener("click", () => {
  resetForm();
});

productList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const product = products.find((item) => item.id === Number(button.dataset.productId));
  if (!product) {
    return;
  }

  if (button.dataset.action === "edit") {
    fillForm(product);
    return;
  }

  if (button.dataset.action === "toggle-active") {
    button.disabled = true;

    try {
      await api(`/api/v1/products/${product.id}`, {
        method: "PATCH",
        body: JSON.stringify({ active: !product.active }),
      });
      await loadProducts();
      setStatus(product.active ? "Produto ocultado da vitrine." : "Produto ativado na vitrine.");
    } catch (error) {
      if (error.status === 401) {
        window.location.href = "/admin";
        return;
      }

      setStatus(error.message || "Nao foi possivel atualizar o produto.", "error");
      button.disabled = false;
    }
  }
});

productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setLoadingState(true);
  setStatus(editingProduct ? "Salvando alteracoes..." : "Salvando produto...");

  try {
    const imageUrl = await uploadImage(imageInput.files?.[0]);
    const payload = buildPayload(imageUrl);
    const path = editingProduct ? `/api/v1/products/${editingProduct.id}` : "/api/v1/products";
    const method = editingProduct ? "PATCH" : "POST";

    await api(path, {
      method,
      body: JSON.stringify(payload),
    });

    setStatus(editingProduct ? "Produto atualizado." : "Produto cadastrado. Ele ja esta na vitrine.");
    resetForm({ keepStatus: true });
    await loadProducts();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "/admin";
      return;
    }

    setStatus(error.message || "Nao foi possivel salvar. Confira os campos obrigatorios.", "error");
  } finally {
    setLoadingState(false);
  }
});

erpReportForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = erpReportInput.files?.[0];
  if (!file) {
    setErpReportStatus("Selecione o relatorio extraido do ERP.", "error");
    return;
  }

  erpReportSubmitButton.disabled = true;
  setErpReportStatus("Enviando relatorio...");

  try {
    const result = await uploadErpReport(file);
    const sizeMb = Number(result.size_bytes || 0) / 1024 / 1024;
    const extractedTextChars = Number(result.extracted_text_chars || 0);
    const importedProducts = Number(result.imported_products || 0);
    const updatedProducts = Number(result.updated_products || 0);
    const importedImages = Number(result.imported_images || 0);
    const extractedTextMessage = extractedTextChars
      ? ` Texto extraido: ${extractedTextChars} caracteres.`
      : "";
    const importMessage =
      importedProducts || updatedProducts
        ? ` Produtos criados: ${importedProducts}. Produtos atualizados: ${updatedProducts}.`
        : " Nenhum produto foi importado.";
    const imageMessage = importedImages ? ` Fotos vinculadas: ${importedImages}.` : "";
    erpReportForm.reset();
    setErpReportStatus(
      `Relatorio enviado: ${result.original_filename} (${sizeMb.toFixed(2)} MB).${extractedTextMessage}${importMessage}${imageMessage}`,
      "success"
    );
    await loadProducts();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "/admin";
      return;
    }

    setErpReportStatus(error.message || "Nao foi possivel enviar o relatorio.", "error");
  } finally {
    erpReportSubmitButton.disabled = false;
  }
});

loadProducts();
