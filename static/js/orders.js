console.log("Orders page loaded")

let currentPage=1;
let isLoading=false;
let selectedOrderId = null;
const pageSize=10;
const nextButton=document.getElementById("next-page");
const previousButton=document.getElementById("previous-page");
const deleteButton = document.getElementById("delete-order-button");

async function loadOrders(){
    const token=sessionStorage.getItem("access_token");
    if(!token){
        alert("Please Login First");
        window.location.href="/demo/login";
        return;
    }
    if(isLoading){
        return;
    }
    isLoading=true;
    const oldNextDisabled=nextButton.disabled;
    const oldPreviousDisabled=previousButton.disabled;
    nextButton.disabled = true;
    previousButton.disabled = true;

    try{
        const response=await fetch(`/orders?page=${currentPage}&limit=${pageSize}&order_by=desc`,{
            headers: {
                "Authorization":"Bearer " + token,
            }
        });
        const data=await response.json();
        if(response.status===401){
                sessionStorage.removeItem("access_token");
                alert("登入已失效,請重新載入");
                window.location.href="/demo/login";
                return;
            }
        if (!response.ok){
            throw new Error("Load orders failed: " + response.status);
        }

        const response2=await fetch(`/orders?page=${currentPage+1}&limit=${pageSize}&order_by=desc`,{
            headers: {
                "Authorization":"Bearer " + token,
            }
        });

        if (!response2.ok){
            throw new Error("Check next page failed: " + response2.status);
        }
        const data2=await response2.json()

        const tableBody=document.getElementById("order-table-body");
        tableBody.replaceChildren();

        const ordersMessage = document.getElementById("orders-message");

        if (data.length === 0) {
            ordersMessage.textContent = "No orders found.";
            ordersMessage.classList.remove("error");
        }else{
            ordersMessage.textContent = "";
            ordersMessage.classList.remove("error");

            data.forEach(function(order){
                const row=document.createElement("tr");

                const idCell=document.createElement("td")
                idCell.textContent=order.id;
                row.appendChild(idCell);

                const productCell=document.createElement("td")
                productCell.textContent=order.product.name;
                row.appendChild(productCell);

                const priceCell=document.createElement("td")
                priceCell.textContent=order.product.price;
                row.appendChild(priceCell);

                const amountCell=document.createElement("td")
                amountCell.textContent=order.amount;
                row.appendChild(amountCell);

                const userCell=document.createElement("td")
                userCell.textContent=order.user.name;
                row.appendChild(userCell);

                const actionCell=document.createElement("td")
                const detailButton=document.createElement("button")
                detailButton.textContent="View detail";
                detailButton.addEventListener("click", function() {
                    loadOrderDetail(order.id).catch(function(error){
                        console.error("Order detail failed:", error);
                        document.getElementById("order-detail-message").textContent =
                            "Load order detail failed: " + error.message;
                    });
                    loadOrderEvents(order.id).catch(function(error){
                        console.error("Order events failed:",error);
                        document.getElementById("order-events-message").textContent =
                            "Load order events failed: " + error.message;
                    })
                });

                actionCell.appendChild(detailButton);
                row.appendChild(actionCell);
                tableBody.append(row);
            })
        }

        const page=document.getElementById("page-number");
        page.textContent=`Page ${currentPage}`;

        previousButton.disabled = currentPage === 1;
        nextButton.disabled = data2.length===0;

    }catch(error){
        nextButton.disabled = oldNextDisabled;
        previousButton.disabled = oldPreviousDisabled;
        throw error;
    }finally{
        isLoading=false;
    }
}
loadOrders().catch(function(error){
    const ordersMessage = document.getElementById("orders-message");
    ordersMessage.textContent="orders loaded failed,please refresh website";
    ordersMessage.classList.add("error");
    console.error("Initial load failed:",error);
})

nextButton.addEventListener("click",function(event){
    if (isLoading){
        return;
    }
    currentPage=currentPage+1;
    loadOrders().catch(function(error) {
        console.error("Next page load failed:", error);
        currentPage = currentPage - 1;

        const ordersMessage = document.getElementById("orders-message");
        ordersMessage.textContent = "Orders load failed. Please try again.";
        ordersMessage.classList.add("error");
    });
});


previousButton.addEventListener("click",function(event){
    if (isLoading){
        return;
    }
    if (currentPage<=1){
        return;
    }
    currentPage=currentPage-1;
    loadOrders().catch(function(error) {
        console.error("Previous page load failed:", error);
        currentPage = currentPage + 1;

        const ordersMessage = document.getElementById("orders-message");
        ordersMessage.textContent = "Orders load failed. Please try again.";
        ordersMessage.classList.add("error");
    });
});

deleteButton.addEventListener("click", async function() {
    if (selectedOrderId === null) {
        return;
    }
    const confirmed = confirm(`Are you sure you want to delete order ${selectedOrderId}?`);

    if (!confirmed) {
        return;
    }
    console.log("Confirmed delete order:", selectedOrderId);
    const token = sessionStorage.getItem("access_token");
    deleteButton.disabled=true;
    let deleteSucceeded = false;
    try{
        const response = await fetch(`/orders/${selectedOrderId}`, {
            method: "DELETE",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!response.ok) {
            throw new Error("Delete order failed: " + response.status);
        }
        deleteSucceeded = true;
        console.log("Order deleted successfully:", selectedOrderId);
        selectedOrderId=null;
        deleteButton.disabled = true;

        document.getElementById("order-detail-message").textContent =
            "Select an order to view details.";
        document.getElementById("order-events-message").textContent =
            "Select an order to view its event status.";

            const checkResponse = await fetch(
            `/orders?page=${currentPage}&limit=${pageSize}&order_by=desc`,
            {
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        if (!checkResponse.ok) {
            throw new Error("Check current page failed: " + checkResponse.status);
        }

        const remainingOrders = await checkResponse.json();

        if (remainingOrders.length === 0 && currentPage > 1) {
            currentPage--;
        }
        await loadOrders();
    }catch(error){
        console.error("Delete order flow failed:", error);
        document.getElementById("order-detail-message").textContent =
        deleteSucceeded
            ? "Order deleted, but refreshing the list failed. Please refresh the page."
            : "Delete failed: " + error.message;
    }finally{
        if (selectedOrderId != null){
            deleteButton.disabled=false;
        }
    }
});

async function loadOrderDetail(orderId){
    const eventsMessage = document.getElementById("order-detail-message");
    eventsMessage.textContent = "Loading order detail...";
    const token=sessionStorage.getItem("access_token");
    const response=await fetch(`/orders/${orderId}`,{
        headers:{
            "Authorization":"Bearer "+ token,
        }
    });
    if(response.status===401){
            sessionStorage.removeItem("access_token");
            alert("登入已失效,請重新載入");
            window.location.href="/demo/login";
            return;
    }
    if (!response.ok) {
        throw new Error("Load order detail failed: " + response.status);
    }
    const data=await response.json();
    console.log("Order Detail",data);

    selectedOrderId = data.id;
    const deleteButton = document.getElementById("delete-order-button");
    deleteButton.disabled = false;

    const detailMessage=document.getElementById("order-detail-message");
    detailMessage.textContent=
    `Order ID: ${data.id} | Product: ${data.product.name} | Price: ${data.product.price} | Amount: ${data.amount} | User: ${data.user.name}`;
};

async function loadOrderEvents(orderId){
    const eventsMessage = document.getElementById("order-events-message");
    eventsMessage.textContent = "Loading order events...";

    const token=sessionStorage.getItem("access_token");
    const response=await fetch(`/orders/${orderId}/events`,{
        headers:{
            "Authorization":"Bearer "+ token,
        }
    });
    if (!response.ok){
        throw new Error("Load event status failed: " + response.status);
    }
    const data=await response.json();
    console.log("Order Events:", data);
    eventsMessage.textContent=
    `Event ID: ${data.event_id} | ` +
    `Type: ${data.event_type} | ` +
    `Status: ${data.status} | ` +
    `Processed: ${data.processed}`;
}
