const productSelect = document.querySelector('[data-testid="product-select"]');
const quantityInput = document.querySelector('[data-testid="quantity"]');
const createOrderButton = document.querySelector('[data-testid="create-order-button"]');
const productsStatus = document.querySelector('[data-testid="products-status"]');
const orderForm = document.querySelector('[data-testid="order-form"]');
const orderMessage = document.querySelector('[data-testid="order-message"]');
const orderNumber = document.querySelector('[data-testid="order-number"]');
const orderStatus = document.querySelector('[data-testid="order-status"]');
const logoutButton = document.querySelector('[data-testid="logout-button"]');

function priceAsNumber(price) {
    const normalized = String(price || "").replace(/[^0-9.]/g, "");
    return normalized || "0.00";
}

async function loadProducts() {
    try {
        const response = await fetch(
            "/coupApply/cms/goodsList?msgType=getHandsetListOfCust&page=1&size=20"
        );
        const payload = await response.json().catch(() => ({}));
        const products = payload.goodsList || [];

        if (!response.ok || payload.error_code !== "0000" || products.length === 0) {
            throw new Error(payload.msg || payload.error || "没有可用商品");
        }

        productSelect.replaceChildren();
        for (const product of products) {
            const option = document.createElement("option");
            option.value = product.goodsId;
            option.textContent = `${product.goods_name}（${product.unit_price}）`;
            option.dataset.price = priceAsNumber(product.unit_price);
            productSelect.appendChild(option);
        }

        productSelect.disabled = false;
        createOrderButton.disabled = false;
        productsStatus.textContent = `已加载 ${products.length} 件商品`;
    } catch (error) {
        productsStatus.textContent = error.message || "商品加载失败";
        productsStatus.classList.add("error");
    }
}

orderForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const selected = productSelect.selectedOptions[0];
    createOrderButton.disabled = true;
    createOrderButton.textContent = "创建中……";
    orderMessage.textContent = "正在提交订单";
    orderNumber.textContent = "-";
    orderStatus.textContent = "-";

    try {
        const response = await fetch("/coupApply/cms/placeAnOrder", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                goods_id: selected.value,
                number: Number(quantityInput.value),
                propertyChildIds: "2:9",
                inviter_id: 127839112,
                price: selected.dataset.price,
                freight_insurance: "0.0",
                discount_code: "002399",
                consignee_info: {
                    name: "张三",
                    phone: 13800000000,
                    address: "北京市海淀区西三环北路74号院4栋3单元1008",
                },
            }),
        });

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload.error_code !== "0000") {
            throw new Error(payload.error || payload.message || "订单创建失败");
        }

        orderMessage.textContent = payload.message;
        orderNumber.textContent = payload.orderNumber;
        orderStatus.textContent = "待支付";
    } catch (error) {
        orderMessage.textContent = error.message || "订单创建失败";
        orderStatus.textContent = "失败";
    } finally {
        createOrderButton.disabled = false;
        createOrderButton.textContent = "创建订单";
    }
});

logoutButton.addEventListener("click", () => {
    sessionStorage.removeItem("taf_user_token");
    window.location.assign("/ui/login");
});

if (!sessionStorage.getItem("taf_user_token")) {
    window.location.replace("/ui/login");
} else {
    loadProducts();
}
