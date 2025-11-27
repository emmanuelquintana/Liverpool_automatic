return (function() {
    const items = [];
    const nameNodes = document.querySelectorAll('div[class*="_OrderItem_item_name__"]');

    nameNodes.forEach((nameDiv, index) => {
        const title = (nameDiv.textContent || "").trim();
        let qtyText = "1";
        let qtyNumber = 1;
        let containerClass = null;
        let qtyLabelText = null;

        // Contenedor del ítem (tarjeta completa)
        let container = nameDiv.closest('div[class*="_OrderItem_item__"]') || nameDiv.parentElement;
        if (container) {
            containerClass = container.className;

            // Buscar dentro del contenedor el label "Cantidad:"
            const labelDivs = container.querySelectorAll('div[class*="_OrderItem_item_label__"]');
            labelDivs.forEach(labelDiv => {
                const label = (labelDiv.textContent || "").trim();
                if (label.toLowerCase().startsWith("cantidad")) {
                    const valueNode = labelDiv.nextElementSibling;
                    if (valueNode) {
                        qtyText = (valueNode.textContent || "").trim();
                        const num = parseInt(qtyText.replace(/[^0-9]/g, ""), 10);
                        if (!Number.isNaN(num)) {
                            qtyNumber = num;
                        }
                    }
                    qtyLabelText = label;
                }
            });
        }

        items.push({
            index,
            title,
            qtyText,
            qtyNumber,
            containerClass,
            qtyLabelText
        });
    });

    return items;
})();
