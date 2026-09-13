return (function() {
    const items = [];
    const nameNodes = document.querySelectorAll('div[class*="_OrderItem_item_name__"]');

    nameNodes.forEach((nameDiv, index) => {
        const title = (nameDiv.textContent || "").trim();
        let qtyText = "1";
        let qtyNumber = 1;
        let containerClass = null;
        let qtyLabelText = null;
        let skuOferta = "";
        let talla = "";
        let skuProducto = "";
        let categoria = "";
        const details = {};

        // Contenedor del ítem (tarjeta completa)
        let container = nameDiv.closest('div[class*="_OrderItem_item__"]') || nameDiv.parentElement;
        if (container) {
            containerClass = container.className;

            // Buscar dentro del contenedor todos los labels de atributos
            const labelDivs = container.querySelectorAll('div[class*="_OrderItem_item_label__"]');
            labelDivs.forEach(labelDiv => {
                const rawLabel = (labelDiv.textContent || "").trim();
                const cleanKey = rawLabel.toLowerCase().replace(/:$/, "").trim();
                const valueNode = labelDiv.nextElementSibling;
                const val = valueNode ? (valueNode.textContent || "").trim() : "";
                
                details[cleanKey] = val;

                if (cleanKey.startsWith("cantidad")) {
                    qtyText = val;
                    const num = parseInt(qtyText.replace(/[^0-9]/g, ""), 10);
                    if (!Number.isNaN(num)) {
                        qtyNumber = num;
                    }
                    qtyLabelText = rawLabel;
                } else if (cleanKey.includes("sku de oferta") || cleanKey.includes("sku oferta")) {
                    skuOferta = val;
                } else if (cleanKey === "talla") {
                    talla = val;
                } else if (cleanKey.includes("sku de producto") || cleanKey.includes("sku producto")) {
                    skuProducto = val;
                } else if (cleanKey.includes("categoría") || cleanKey.includes("categoria")) {
                    categoria = val;
                }
            });
        }

        if (!skuOferta && details["sku"]) {
            skuOferta = details["sku"];
        }

        items.push({
            index,
            title,
            qtyText,
            qtyNumber,
            skuOferta,
            talla,
            skuProducto,
            categoria,
            details,
            containerClass,
            qtyLabelText
        });
    });

    return items;
})();
