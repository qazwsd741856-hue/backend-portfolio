const orderInput = document.getElementById("order-id");
const searchButton = document.getElementById("search-event-button");
const eventMessage = document.getElementById("event-message");
const eventResult = document.getElementById("event-result");


searchButton.addEventListener("click", async function() {

    eventMessage.textContent = "";
    eventResult.hidden = true;

    if (!orderInput.checkValidity()) {
        orderInput.reportValidity();
        return;
    }
    const orderId = Number(orderInput.value);
    const token = sessionStorage.getItem("access_token");
    if (!token) {
            alert("Please login first");
            window.location.href = "/demo/login";
            return;
        }

    searchButton.disabled = true;
    searchButton.textContent = "Searching...";

    try{
        const response=await fetch(`/orders/${orderId}/events`,{
            headers:{
                "Authorization":"Bearer " + token,
            }
        });
        if (response.status===401){
            sessionStorage.removeItem("access_token");
            alert("登入已失效,請重新載入");
            window.location.href="/demo/login";
            return;
        }
        if (!response.ok){
            const errorData = await response.json();
            throw new Error(errorData.detail ?? `HTTP ${response.status}`);
        }
        const data = await response.json()

        document.getElementById("result-order-id").textContent = data.order_id;
        document.getElementById("result-event-id").textContent = data.event_id;
        document.getElementById("result-event-type").textContent = data.event_type;
        document.getElementById("result-status").textContent = data.status;
        document.getElementById("result-processed").textContent = data.processed;
        document.getElementById("result-created-at").textContent = data.created_at;
        document.getElementById("result-sent-at").textContent = data.sent_at ?? "-";
        document.getElementById("result-processed-at").textContent = data.processed_at ?? "-";

        eventResult.hidden = false;

    }catch(error){
        console.error("Load event failed: ",error);
        eventMessage.textContent =
        error.message;
    }finally{
        searchButton.disabled = false;
        searchButton.textContent = "Search";
    }
});
