console.log("Admin page loaded")

async function loadAdminUsers() {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
        alert("Please login first");
        window.location.href = "/demo/login";
        return;
    }

    const response = await fetch("/admin/users", {
        headers: {
            "Authorization": "Bearer " + token
        }
    });
    if(response.status===403){
            alert("權限不足，需管理者登入");
            window.location.href="/";
            return;
    }
    if(response.status===401){
            sessionStorage.removeItem("access_token");
            alert("登入已失效,請重新載入");
            window.location.href="/demo/login";
            return;
    }
    if (!response.ok) {
        throw new Error("Load admin users failed: " + response.status);
    }

    const data = await response.json();
    console.log("Admin Users:", data);

    const tableBody=document.getElementById("admin-users-body");
    tableBody.replaceChildren();

    data.forEach(function(user){
        const row=document.createElement("tr");

        const idCell=document.createElement("td");
        idCell.textContent=user.id;
        row.appendChild(idCell);

        const nameCell = document.createElement("td");
        nameCell.textContent = user.name;
        row.appendChild(nameCell);

        const emailCell = document.createElement("td");
        emailCell.textContent = user.email;
        row.appendChild(emailCell);

        const roleCell = document.createElement("td");
        roleCell.textContent = user.role;
        row.appendChild(roleCell);

        const activeCell = document.createElement("td");
        activeCell.textContent = user.is_active;
        row.appendChild(activeCell);

        const actionCell = document.createElement("td");
        const roleSelect = document.createElement("select");

        const userOption = document.createElement("option");
        userOption.value = "user";
        userOption.textContent = "user";

        const adminOption = document.createElement("option");
        adminOption.value = "admin";
        adminOption.textContent = "admin";

        roleSelect.appendChild(userOption);
        roleSelect.appendChild(adminOption);
        roleSelect.value=user.role;

        const saveButton = document.createElement("button");
        saveButton.textContent = "Save Role";

        saveButton.addEventListener("click", async function() {
            const token = sessionStorage.getItem("access_token");
            if (roleSelect.value===user.role){
                return;
            };
            const confirmed=confirm(
                `Change ${user.name}'s role from ${user.role} to ${roleSelect.value}?`
            );
            if (!confirmed){
                roleSelect.value=user.role;
                return;
            }
            saveButton.disabled=true;
            try{
                const response = await fetch(`/admin/users/${user.id}/role`,{
                    method:"PATCH",
                    headers: {
                        "Authorization":"Bearer " + token,
                        "Content-Type":"application/json"
                    },
                    body: JSON.stringify({
                        role:roleSelect.value,
                    })
                })
                if(response.status===401){
                sessionStorage.removeItem("access_token");
                alert("登入已失效,請重新載入");
                window.location.href="/demo/login";
                return;
                }
                if (!response.ok){
                    throw new Error("Update role failed: " + response.status)
                }
                const data=await response.json();
                console.log("Updated User:", data);

                roleCell.textContent = data.role;
                user.role = data.role;
                roleSelect.value = data.role;

            }catch(error){
                console.error("Update role failed:", error);
                alert("Update role failed: " + error.message);

                roleSelect.value = user.role;
            }finally{
                saveButton.disabled=false;
            }
        });
        const statusButton = document.createElement("button");

        statusButton.textContent = user.is_active
            ? "Deactivate"
            : "Activate";

        statusButton.addEventListener("click", async function() {
            const newStatus = !user.is_active;

            const confirmed = confirm(
                `Change ${user.name}'s active status to ${newStatus}?`
            );

            if (!confirmed) {
                return;
            }

            const token = sessionStorage.getItem("access_token");
            statusButton.disabled = true;

            try {
                const response = await fetch(`/admin/users/${user.id}/status`, {
                    method: "PATCH",
                    headers: {
                        "Authorization": "Bearer " + token,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        is_active: newStatus
                    })
                });

                if (response.status === 401) {
                    sessionStorage.removeItem("access_token");
                    alert("登入已失效，請重新登入");
                    window.location.href = "/demo/login";
                    return;
                }

                if (!response.ok) {
                    throw new Error("Update status failed: " + response.status);
                }

                const data = await response.json();
                console.log("Updated User Status:", data);

                user.is_active = data.is_active;
                activeCell.textContent = data.is_active;

                statusButton.textContent = data.is_active
                    ? "Deactivate"
                    : "Activate";

            } catch (error) {
                console.error("Update status failed:", error);
                alert("Update status failed: " + error.message);

            } finally {
                statusButton.disabled = false;
            }
        });

        actionCell.appendChild(roleSelect);
        actionCell.appendChild(saveButton);
        actionCell.appendChild(statusButton);
        row.append(actionCell);
        tableBody.appendChild(row);

    });
}

loadAdminUsers().catch(function(error) {
    console.error("Admin users failed:", error);

    document.getElementById("admin-message").textContent =
        "Load admin users failed: " + error.message;
});
