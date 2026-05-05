// item_capture_rect.js
// Este script se ejecuta al nivel superior y usa `arguments[0]`
// que es como Selenium pasa los parámetros a execute_script(...).

function getItemRoots() {
  const roots = Array.from(
    document.querySelectorAll("div.MuiGrid-root.MuiGrid-container")
  );
  // Solo los que tienen nombre de ítem
  return roots.filter(root =>
    root.querySelector('div[class*="_OrderItem_item_name__"]')
  );
}

function getRect(el) {
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {
    left: r.left,
    top: r.top,
    width: r.width,
    height: r.height,
  };
}

function findProductImage(root) {
  const oldMedia = root.querySelector(".MuiCardMedia-root");
  if (oldMedia) return oldMedia;

  const images = Array.from(root.querySelectorAll("img[src]"));
  return (
    images.find(img => {
      const src = img.getAttribute("src") || "";
      return /liverpool\.com\.mx|\/xl\//i.test(src);
    }) ||
    images.find(img => img.getBoundingClientRect().width > 0 && img.getBoundingClientRect().height > 0) ||
    null
  );
}

// index viene directamente de Selenium: driver.execute_script(..., item_index)
const index = arguments[0];
const itemRoots = getItemRoots();

const debugBase = {
  ok: false,
  index: index,
  rootCount: itemRoots.length,
};

if (!itemRoots.length) {
  return {
    ...debugBase,
    error: "no_item_roots",
    message:
      'No se encontraron div.MuiGrid-root.MuiGrid-container con _OrderItem_item_name__',
  };
}

if (typeof index !== "number" || index < 0 || index >= itemRoots.length) {
  return {
    ...debugBase,
    error: "index_out_of_range",
    message: "El índice solicitado no existe en itemRoots",
  };
}

const root = itemRoots[index];

// Imagen y título del producto
const imgEl = findProductImage(root);
const titleEl = root.querySelector('div[class*="_OrderItem_item_name__"]');

// Todas las secciones tipo título dentro del ítem
const sectionTitleEls = Array.from(
  root.querySelectorAll('div[class*="_OrderItem_item_title__"]')
);
const sectionTitlesText = sectionTitleEls.map(el => el.textContent.trim());

// Buscamos específicamente "Detalle del producto"
const detailTitleEl = sectionTitleEls.find(el =>
  el.textContent.trim().toLowerCase().includes("detalle del producto")
);

// Tratamos de encontrar el contenedor de detalle
let detailContainer = null;
if (detailTitleEl) {
  let node = detailTitleEl.parentElement;
  while (node && node !== root) {
    if (node.querySelector('div[class*="_OrderItem_item_container__"]')) {
      detailContainer = node;
      break;
    }
    node = node.parentElement;
  }
}

const rects = [];

// Agregamos rects válidos (imagen, título, contenedor de detalle, filas internas)
if (imgEl) rects.push(getRect(imgEl));
if (titleEl) rects.push(getRect(titleEl));
if (detailContainer) {
  rects.push(getRect(detailContainer));
  const rows = Array.from(
    detailContainer.querySelectorAll(
      'div[class*="_OrderItem_item_container__"]'
    )
  );
  rows.forEach(row => rects.push(getRect(row)));
}

// Filtramos rects no válidos
const validRects = rects.filter(
  r => r && r.width > 0 && r.height > 0
);

if (!validRects.length) {
  return {
    ...debugBase,
    error: "no_valid_rects",
    message: "No se pudieron calcular rectángulos válidos",
    hasImg: !!imgEl,
    hasTitle: !!titleEl,
    hasDetailTitle: !!detailTitleEl,
    sectionTitlesText,
  };
}

const padding = 8;
const left = Math.min(...validRects.map(r => r.left)) - padding;
const top = Math.min(...validRects.map(r => r.top)) - padding;
const right = Math.max(...validRects.map(r => r.left + r.width)) + padding;
const bottom = Math.max(...validRects.map(r => r.top + r.height)) + padding;

return {
  ok: true,
  index,
  rootCount: itemRoots.length,
  hasImg: !!imgEl,
  hasTitle: !!titleEl,
  hasDetailTitle: !!detailTitleEl,
  sectionTitlesText,
  left,
  top,
  width: right - left,
  height: bottom - top,
};
