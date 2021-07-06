const status_btn = document.getElementsByClassName("status_btn")
const input_status = document.getElementById("hidden_status")
const form_field = document.getElementById("form-field")

for(var i=0;i<status_btn.length;i++){
    status_btn[i].addEventListener("click",function(){
        const status = this.dataset.status
        form_field.setAttribute("id",status)
        form_field.setAttribute("aria-labelledby",status)
        input_status.value = status
    })
}

let url = new URL(window.location)
let parms = new URLSearchParams(url.search)
let status = parms.get("status")

if(status){
    const active_btn = document.getElementById(`${status}-tab`)
    form_field.setAttribute("id",status)
    form_field.classList.add("active")
    form_field.classList.add("show")
    active_btn.classList.add("active")
}


