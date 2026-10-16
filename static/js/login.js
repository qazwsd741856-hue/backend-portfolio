const loginForm=document.getElementById("login-form");

loginForm.addEventListener("submit",async function(event){
    event.preventDefault();
    const email=loginForm.elements["email"].value;
    const password=loginForm.elements["password"].value;

    const formData=new URLSearchParams();
    formData.append("username",email);
    formData.append("password",password);

    const response=await fetch("/users/login",{
        method:"POST",
        body:formData});
    const data=await response.json();
    if (!response.ok){
        console.log("Login failed",data.detail);
        return;
    }
    sessionStorage.setItem("access_token",data.access_token);
    console.log("token-storaged ");
    window.location.href="/";
});
