const registerFrom=document.getElementById("register-form")
const registerMessage = document.getElementById("register-message");

registerFrom.addEventListener("submit",async function(event){
    event.preventDefault();

    const name=registerFrom.elements["name"].value;
    const email=registerFrom.elements["email"].value;
    const password=registerFrom.elements["password"].value;

    registerMessage.textContent="";
    registerMessage.classList.remove("success");
    registerMessage.classList.remove("error");
    try{
        const response=await fetch("/users",{
            method:"POST",
            headers:{
                "Content-Type": "application/json"
            },
            body:JSON.stringify({
                "name":name,
                "email":email,
                "password":password,
            })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail ?? `HTTP:${response.status}`);
        } 
        registerMessage.textContent = "註冊成功！請前往登入。";
        registerMessage.classList.add("success");
        alert("註冊成功！請前往登入。");
        window.location.href="/demo/login";
    }catch(error){
        console.error("Create failed:",error);
        registerMessage.textContent ="Create account failed: " + error.message;
        registerMessage.classList.add("error");
    }
})