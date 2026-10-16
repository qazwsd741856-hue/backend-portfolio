console.log("welcome")
let currentPage=1;
const pageSize=10;
const previousButton=document.getElementById("previous-page");
const nextButton=document.getElementById("next-page");
const page=document.getElementById("page-number");
const productMessage=document.getElementById("products-message");
let isLoading=false;

async function loadProducts(){
    if (isLoading){
        return;
    }
    isLoading=true;

    const oldPreviousButton=previousButton.disabled;
    const oldNextButton=nextButton.disabled;
    previousButton.disabled=true;
    nextButton.disabled=true;
    try{
        const response=await fetch(`/products?page=${currentPage}&limit=${pageSize}&order_by=asc`,);
        if(!response.ok){
            throw new Error("Load products failed: "+response.status);
        }
        const data=await response.json();

        const response2=await fetch(`/products?page=${currentPage+1}&limit=${pageSize}&order_by=asc`,);
        if(!response2.ok){
            throw new Error("Check next page failed: "+response2.status);
        }
        const data2=await response2.json();

        const tableBody=document.getElementById("product-table-body");
        tableBody.replaceChildren();

        data.items.forEach(function(product){
            const row=document.createElement("tr");

            const idCell=document.createElement("td");
            idCell.textContent=product.id;
            row.appendChild(idCell);

            const nameCell=document.createElement("td");
            nameCell.textContent=product.name;
            row.appendChild(nameCell);

            const priceCell=document.createElement("td");
            priceCell.textContent=product.price;
            row.appendChild(priceCell);
            const stockCell=document.createElement("td");
            stockCell.textContent=product.stock;
            row.appendChild(stockCell);

            tableBody.appendChild(row);
        })
        page.textContent="Page "+ currentPage;
        const productMessage=document.getElementById("products-message");
        productMessage.textContent="";
        productMessage.classList.remove("error");

        previousButton.disabled= currentPage===1;
        nextButton.disabled= data2.items.length===0;


    }catch(error){
        nextButton.disabled = oldNextDisabled;
        previousButton.disabled = oldPreviousDisabled;
        throw error;
    }finally{
        isLoading=false;
    }
}
loadProducts().catch(function(error){
    const productMessage=document.getElementById("products-message");
    productMessage.textContent="products loaded failed,please refresh website";
    productMessage.classList.add("error");
    console.error("Initial load failed:",error);
});

async function loadOrderEvent(orderId){
    const token=sessionStorage.getItem("access_token");
    const response=await fetch(`/orders/${orderId}/events`,{
        headers:{
            "Authorization":"Bearer "+token,
        }
    });
    if (!response.ok){
        throw new Error("Load order event failed: " +response.status );
    }
    const data=await response.json();
    return data;
    }
let pollingTimer=null;
let pollingVersion=0;

function stopPolling(){
    pollingVersion=pollingVersion+1;

    if (pollingTimer !== null){
        clearTimeout(pollingTimer);
        pollingTimer=null;
    }
}
async function pollOrderEvent(orderId,attempt=1,myVersion=pollingVersion){
    try{
        const data=await loadOrderEvent(orderId);
        if (myVersion !== pollingVersion) {
            console.log(
                "Old polling ignored:",
                "orderId =", orderId,
                "myVersion =", myVersion,
                "pollingVersion =", pollingVersion
            );
            return;
        }
        const eventOrderId = document.getElementById("event-order-id");
        const eventId = document.getElementById("event-id");
        const eventSection=document.getElementById("event-section");
        const eventMessage=document.getElementById("event-message");

        eventOrderId.textContent = orderId;
        eventId.textContent = data.event_id;
        eventSection.hidden=false;

        eventMessage.classList.remove(
        "event-processing",
        "event-completed",
        "event-timeout",
        "event-failed"
        );
        if (data.processed===true){
            eventMessage.textContent="Completed";
             eventMessage.classList.add("event-completed")
        }else{
            eventMessage.textContent="Processing...";
            eventMessage.classList.add("event-processing")
        }

        if (data.processed==true){
            console.log("Worker processed event, polling stopped.");
            return;
        }
        if (attempt >=15){
            console.warn("Polling stopped: maximum attempts reached.");

            eventMessage.textContent="Timed out";
            eventMessage.classList.remove("event-processing")
            eventMessage.classList.add("event-timeout")
                return;
        }
        pollingTimer=setTimeout(function(){
            pollOrderEvent(orderId,attempt+1,myVersion);
        },2000)
    }catch(error){
        if (myVersion !== pollingVersion){
            return;
        }
        console.error("Polling failed:", error)
        const eventSection=document.getElementById("event-section");
        const eventMessage=document.getElementById("event-message");
        const eventOrderId = document.getElementById("event-order-id");
        const eventId = document.getElementById("event-id");
        eventSection.hidden=false;
        eventMessage.classList.remove(
            "event-processing",
            "event-completed",
            "event-timeout",
            "event-failed"
        );
        eventOrderId.textContent=orderId;
        eventId.textContent="-"
        eventMessage.textContent="Polling failed. Please try again later.";
        eventMessage.classList.add("event-failed")
    }
}
const orderForm =document.getElementById("order-form");
const orderMessage=document.getElementById("order-message");
const submitButton=orderForm.querySelector('button[type="submit"]');
orderForm.addEventListener("submit",async function(event){
    event.preventDefault();
    if (submitButton.disabled) {
    return;}
    const id=Number(orderForm.elements["product_id"].value);
    const amount=Number(orderForm.elements["amount"].value);
    if (!Number.isInteger(id) || id<=0){
        console.log("Product ID 必須正整數");
        orderMessage.textContent = "Product ID must be a positive integer.";
        orderMessage.classList.add("error");
        orderMessage.classList.remove("success");
        const eventSection=document.getElementById("event-section");
        eventSection.hidden=true;
        return;
    }
    if (!Number.isInteger(amount) || amount<=0){
        console.log("amount 必須是正整數");
        orderMessage.textContent = "amount must be a positive integer.";
        orderMessage.classList.add("error");
        orderMessage.classList.remove("success");
        const eventSection=document.getElementById("event-section");
        eventSection.hidden=true;
        return;
    }

    const orderData={
        product_id:id,
        amount:amount
    };
    // console.log(orderData)
    // console.log(JSON.stringify(orderData))
    // console.log(typeof JSON.stringify(orderData));

    const token=sessionStorage.getItem("access_token");
    if(!token){
        alert("Please Login First");
        window.location.href="/demo/login"
        return;
    }
    submitButton.disabled = true;
    submitButton.textContent = "Creating...";
    try{
        const response=await fetch("/orders",{
                method:"POST",
                headers:{
                    "Authorization":"Bearer " + token,
                    "Content-Type": "application/json"
                },
                body:JSON.stringify(orderData)
            });
        const data=await response.json();

        if(response.status===401){
            sessionStorage.removeItem("access_token");
            alert("登入已失效,請重新載入");
            window.location.href="/demo/login";
            return;
        }
        if(!response.ok){
            stopPolling();

            const eventSection = document.getElementById("event-section");
            eventSection.hidden = true;
            orderMessage.textContent="Order created failed:"+data.detail;
            orderMessage.classList.add("error");
            orderMessage.classList.remove("success");
            return;
        }
        orderMessage.textContent="Order created successfully!";
        orderMessage.classList.add("success");
        orderMessage.classList.remove("error");

        stopPolling();
        const eventSection = document.getElementById("event-section");
        const eventOrderId = document.getElementById("event-order-id");
        const eventId = document.getElementById("event-id");
        const eventMessage = document.getElementById("event-message");

        eventSection.hidden = false;

        eventOrderId.textContent = data.id;
        eventId.textContent = "-";
        eventMessage.textContent = "Processing...";

        eventMessage.classList.remove(
            "event-processing",
            "event-completed",
            "event-timeout",
            "event-failed"
        );
        eventMessage.classList.add("event-processing");

        pollOrderEvent(data.id);
        try{
            await loadProducts();
        }catch(error){
            console.error("Refresh products failed:", error);
            orderMessage.textContent = "Order created,but product updated failed,please refresh webpage"
            orderMessage.classList.remove("error");
            orderMessage.classList.add("success");
        }
    }catch(error){
        stopPolling();

        const eventSection = document.getElementById("event-section");
        eventSection.hidden = true;
        console.log("Request error:",error);
        orderMessage.textContent="Request failed. Please check your connection";
        orderMessage.classList.add("error");
        orderMessage.classList.remove("success");
    }finally{
        submitButton.disabled = false   ;
        submitButton.textContent = "Create Order";
    }
});

previousButton.addEventListener("click",function(event){
    if (isLoading){
        return;
    }
    if (currentPage <=1){
        return;
    }
    currentPage=currentPage-1;

    loadProducts().catch(function(error){
        console.error("Previous page load failed:", error)
        currentPage=currentPage+1;

        productMessage.textContent= "Products load failed. Please try again.";
        productMessage.classList.add("error");
    });

})

nextButton.addEventListener("click",function(event){
    if (isLoading){
        return;
    }
    currentPage=currentPage+1;

    loadProducts().catch(function(error){
        console.error("Next page load failed:", error)
        currentPage=currentPage-1;

        productMessage.textContent= "Products load failed. Please try again.";
        productMessage.classList.add("error");
    });

})
