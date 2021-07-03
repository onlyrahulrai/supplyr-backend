var approvalButton = document.getElementsByClassName("approvalbutton");
var seller_profile_approve = document.getElementById("seller_profile_approve");
var approve_button = document.getElementById("approve_button");
var approve_form = document.getElementById("approve_form")
var comments = document.getElementById("comments")

for (i = 0; i < approvalButton.length; i++) {
  approvalButton[i].addEventListener("click", function () {
    var sellerProfileId = this.dataset.id;
    var action = this.dataset.action;
    seller_profile_approve.classList.add(action);
    if (action === "rejected" || action === "need_more_info" || action === "permanently_rejected") {
      comments.required = true;
      approve_button.classList.remove("btn-info")
      approve_button.classList.add("btn-success")
      
    } else if (action === "approved") {
        approve_button.classList.remove("btn-danger")
        approve_button.classList.add("btn-info");
    }
    if(action === "need_more_info"){
      approve_button.innerText = "Need more Info";
    }else if(action === "permanently_rejected"){
      approve_button.innerText = "Permanently Rejected";
    }else{
      approve_button.innerText = action;
    }
    approve_form.addEventListener("submit",() => {
        event.preventDefault()
        var comment = comments.value
        console.log(sellerProfileId,action,comment,user)
        approved(sellerProfileId,action,comment,user)
    })
  });
}

function approved(sellerProfileId, action,comment,user) {
  var url = "/v1/reviewer/approve-seller/";
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ sellerProfileId: sellerProfileId, action: action,comment:comment,userId:user }),
  })
    .then((res) => res.json())
    .then((data) => {
        location.reload()
    })
    .catch((error) => console.log(error));
}



