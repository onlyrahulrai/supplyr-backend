const entity_category = document.getElementById("entity_category_filter");
const entity_type = document.getElementById("entity_type_filter");
const gst_enrolled = document.getElementById("is_gst_enrolled_filter");
const active = document.getElementById("is_active_filter");
var searchInput = document.getElementById("search_filter");
const form = document.querySelector("#form-filter");
const filterTab = document.getElementById("filter-tab")
const tabBtn = document.getElementsByClassName("tab-btn")
const tabBody = document.getElementById("tab-body")
const table_body = document
  .getElementById("table-body").getElementsByTagName("tbody")[0];
  

const resetFilter = document.getElementById("reset-filter")
const filterForm = document.getElementsByClassName("filter-form")

const thead_th = document.getElementsByClassName("sort")

var url;
var status;
var search="";


// It is used to hide the filter Start
resetFilter.addEventListener("click",function(){
    resetFilter.classList.add("d-none")
    url = "/reviewer/seller_profiles/"
    filterForm[0].classList.remove("show","active")
    fetchData(url)
    status = ""
    for(var i=0;i<tabBtn.length;i++){
        if (tabBtn[i].classList.contains("active")){
            tabBtn[i].classList.remove("active")
        }
    }
    for(var i = 0;i<thead_th.length;i++){
        thead_th[i].classList.remove("table-column-color")
    }
    form.reset()
})
// It is used to hide the filter End


// Filter accroding to the Table Head field start
for(var i = 0;i<thead_th.length;i++){
    thead_th[i].addEventListener("click",function(){
        resetFilter.classList.remove("d-none")
        const order = this.dataset.sort;
        const name = this.dataset.name;
        const id = this.dataset.id;

        if(order === "asc"){
            thead_th[id].setAttribute("data-sort","desc")
            url = `/reviewer/seller_profiles/?search=${search.replace(" ","+")}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}&status=${status}&sort=${name}`;

        } 
        else if(order === "desc"){
            thead_th[id].setAttribute("data-sort","asc")
            url = `/reviewer/seller_profiles/?search=${search.replace(" ","+")}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}&status=${status}&sort=-${name}`;
        }
        for(var i = 0;i<thead_th.length;i++){
            thead_th[i].classList.remove("table-column-color")
        }
        fetchData(url)
        thead_th[id].classList.toggle("table-column-color")
    })
    
}
// Filter accroding to the Table Head field end


// Preventing the form for refresh Start

form.addEventListener("submit",function(){
    event.preventDefault()
})

// Preventing the form for refresh End

// It handle status button clicked operation Start
for(var i=0;i<tabBtn.length;i++){
    tabBtn[i].addEventListener("click",function(){
        const action = this.dataset.action;
        tabBody.setAttribute("id",action)
        tabBody.setAttribute("aria-labelledby",action)
        url = `/reviewer/seller_profiles/?status=${action}&search=${search.replace(" ","+")}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}`;
        fetchData(url)
        status = action
        resetFilter.classList.remove("d-none")
    })
}

// It handle status button clicked operation End

// Implement the debouncing for search field delay in execution Start

function debounce(func, timeout = 1000){
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
  }
function saveInput(){
    search = searchInput.value.replace(" ","+");
    url = `/reviewer/seller_profiles/?search=${search.replace(" ","+")}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}&status=${status}`;
    fetchData(url)
}
const processChange = debounce(() => saveInput());

// Implement the debouncing for search field delay in execution End

// Prevent Search input field change Start
searchInput.addEventListener("change",function(event){
    event.preventDefault()
    event.stopPropagation();
})
// Prevent Search input field change End


// It is trigger when any change happen in the form filter Start
form.addEventListener("change", function(event){
    url = `/reviewer/seller_profiles/?search=${search.replace(" ","+")}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}&status=${status}`;
        fetchData(url)
        table_body.HTML = ""
})
// It is trigger when any change happen in the form filter Start

// It is used to load data inside a table Start
window.addEventListener("load", function () {
    url = "/reviewer/seller_profiles/";
    fetchData(url)
});

function fetchData(url){
    console.log(url)
    fetch(url, {
        method: "GET",
        headers: {
        "Content-Type": "application/json",
        },
    })
    .then((res) => res.json())
    .then((data) => displayTable(data))
    .catch((error) => console.log(error));   
}


// It is used to display table in home page Start
function displayTable(data) {
    var tbody = ""
    for (var i = 0; i < data.results.length; i++) {
        const child = `
            <tr>
                <td class="id">${data.results[i].id}</td>
                <td class="owner">${data.results[i].owner_name}</td>
                <td class="owner">${data.results[i].owner_email}</td>
                <td class="owner">${data.results[i].owner_phone}</td>
                <td class="business_name">${data.results[i].business_name}</td>
                <td class="entity_category">
                    ${ (data.results[i].entity_category === "M" && "Manufacturer") || (data.results[i].entity_category === "W" && "Wholeseller") || (data.results[i].entity_category === "D" && "Distributer") }
                </td>
                <td class="entity_type">
                    ${ (data.results[i].entity_type === "pvtltd" && "Private Limited") || (data.results[i].entity_type === "llp" && "Limited Liablity Partnership") || (data.results[i].entity_type === "part" && "Partnership") || (data.results[i].entity_type === "prop" && "Propertieship")}
                </td>
                <td class="is_gst_enrolled">
                    ${ data.results[i].is_gst_enrolled  ? "Yes" : "No" }
                </td>
                <td class="status" style="text-transform: capitalize;
                ">${data.results[i].status.replace(/_/g," ")}</td>
                <td><a class="btn btn-sm btn-info btn-sm" href="/reviewer/customer/${data.results[i].id}">View</a></td>
            </tr>
        `;
        tbody += child
    }
    table_body.innerHTML = tbody
    const page = document.getElementById("page")
    page.innerHTML = `Showing ${data.start} to ${data.end} of ${data.totalItems} entries`
    paginator(data)
}
// It is used to display table in home page End


// It's display the pagination button on the reviewer dashboard page Start
function paginator(data){
    let pager = ``
    if(data.previous){
        pager += `<button type="button" class="btn btn-outline-info btn-sm mb-4 page-pagination " onclick="paginationAction(1)"  >First</button>` +
        `<button type="button" class="btn btn-sm btn-outline-info mb-4 page-pagination" onclick="paginationAction(${data.currentPage - 1})" >Previous</button>`
    }

    for(var num=1;num<=data.pageRange.length;num++){
        if(data.currentPage == num){
            pager += `
                <button type="button" class="btn btn-info btn-sm mb-4 page-pagination" onclick="paginationAction(${num})" >${num}</button>
            `
        }
        else if((num > data.currentPage-3) && (num <  data.currentPage+3)){
            pager += `<button type="button" class="btn btn-outline-info btn-sm mb-4 page-pagination" onclick="paginationAction(${num})" >${num}</button>`
        }
    }

    if(data.next){
        pager += `<button type="button" class="btn btn-sm btn-outline-info mb-4 page-pagination" onclick="paginationAction(${data.currentPage + 1} )">Next</button>`+
        `<button type="button" class="btn btn-sm btn-outline-info mb-4 page-pagination" onclick="paginationAction(${data.pageRange.length})">Last</button>`
    }

    const pagination_fields = document.getElementById("pagination_field")
    pagination_fields.innerHTML = pager
}
// It's display the pagination button on the reviewer dashboard page End

// It's handle the pagination each button click Start
function paginationAction(page){
    if(url.includes("&")){
        fetchUrl = `${url}/&page=${page}`
    }else{
        fetchUrl = `${url}?page=${page}`
    }
    fetchData(fetchUrl)
}
// It's handle the pagination each button click End
