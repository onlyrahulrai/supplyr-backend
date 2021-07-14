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

var url;
var status;
var search;


const btn_prev = document.getElementById("btn_prev")
const btn_next = document.getElementById("btn_next")

// It is used to hide the filter Start
resetFilter.addEventListener("click",function(){
    url = "http://127.0.0.1:8000/v1/reviewer/seller_profiles/"
    filterForm[0].classList.remove("show","active")
    fetchData(url)
    for(var i=0;i<tabBtn.length;i++){
        if (tabBtn[i].classList.contains("active")){
            tabBtn[i].classList.remove("active")
        }
    }
})
// It is used to hide the filter End


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
        url = `http://127.0.0.1:8000/v1/reviewer/seller_profiles/?status=${action}`;
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
    url = `http://127.0.0.1:8000/v1/reviewer/seller_profiles/?search=${search.replace(" ","+")}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}&status=${status}`;
    fetchData(url)
}
const processChange = debounce(() => saveInput());

// Implement the debouncing for search field delay in execution End

// Prevenvt Search input field change Start
searchInput.addEventListener("change",function(event){
    event.preventDefault()
    event.stopPropagation();
})
// Prevenvt Search input field change End


// It is trigger when any change happen in the form filter Start
form.addEventListener("change", function(event){
    url = `http://127.0.0.1:8000/v1/reviewer/seller_profiles/?search=${searchInput.value}&entity_category=${entity_category.value}&entity_type=${entity_type.value}&is_gst_enrolled=${gst_enrolled.value}&is_active=${active.value}&status=${status}`;
        fetchData(url)
        table_body.HTML = ""
})
// It is trigger when any change happen in the form filter Start





// It is used to load data inside a table Start
window.addEventListener("load", function () {
    url = "http://127.0.0.1:8000/v1/reviewer/seller_profiles/";
    fetchData(url)
});

function fetchData(url){
    fetch(url, {
        method: "GET",
        headers: {
        "Content-Type": "application/json",
        },
    })
    .then((res) => res.json())
    .then((data) => pagination(data))
    .catch((error) => console.log(error));
}

// Pagination STart

var current_page = 1;
var records_per_page = 5;

function pagination(objJson){ 
    btn_prev.addEventListener("click",() => {
        if (current_page > 1) {
            current_page--;
            changePage(current_page);
        }
    })
    btn_next.addEventListener("click",() => {
        if (current_page < numPages()) {
            current_page++;
            changePage(current_page);
        }
    }) 

        function changePage(page)
        {
        var btn_next = document.getElementById("btn_next");
        var btn_prev = document.getElementById("btn_prev");
        var listing_table = document.getElementById("listingTable");
        var page_span = document.getElementById("page");

        // Validate page
        if (page < 1) page = 1;
        if (page > numPages()) page = numPages();

        listing_table.innerHTML = "";
        var tbody = ""

            if(objJson.length > 0){
                for (var i = (page-1) * records_per_page; i < (page * records_per_page); i++) {
                    if (objJson.length  > i){
                        const child = `
                            <tr>
                                <td>${objJson[i].owner}</td>
                                <td>${objJson[i].business_name}</td>
                                <td>
                                    ${ (objJson[i].entity_category === "M" && "Manufacturer") || (objJson[i].entity_category === "W" && "Wholeseller") || (objJson[i].entity_category === "D" && "Distributer") }
                                </td>
                                <td>
                                    ${ (objJson[i].entity_type === "pvtltd" && "Private Limited") || (objJson[i].entity_type === "llp" && "Limited Liablity Partnership") || (objJson[i].entity_type === "part" && "Partnership") || (objJson[i].entity_type === "prop" && "Propertieship")}
                                </td>
                                <td>
                                    ${ objJson[i].is_gst_enrolled  ? "Yes" : "No" }
                                </td>
                                <td>
                                    ${ objJson[i].is_active ? "Yes" : "No" }
                                </td>
                                <td style="text-transform: capitalize;
                                ">${objJson[i].status.replace(/_/g," ")}</td>
                                <td><a class="btn btn-sm btn-info btn-sm" href="/v1/reviewer/customer/${objJson[i].id}">View</a></td>
                            </tr>
                        `;
                        tbody += child
                    }
                }
                table_body.innerHTML = tbody
                page_span.innerHTML = `${page} of ${numPages()}` ;
            }else{
                table_body.innerHTML = ""
                page_span.innerHTML = `${page} of 1` ;
            }

            
            if (page === 0 || page === 1) {
                btn_prev.style.visibility = "hidden";
            } else {
                btn_prev.style.visibility = "visible";
            }

            if (page === numPages()) {
                btn_next.style.visibility = "hidden";
            } else {
                btn_next.style.visibility = "visible";
            }
        }

        function numPages()
        {
            return Math.ceil(objJson.length / records_per_page);
        }

        changePage(1);
}

// Pagination End

// It is used to load data inside a table Start

// function displayTable(data) {
//     var tbody = ""
//     for (var i = 0; i < data.length; i++) {
//         const child = `
//             <tr>
//                 <td>${data[i].owner}</td>
//                 <td>${data[i].business_name}</td>
//                 <td>
//                     ${ (data[i].entity_category === "M" && "Manufacturer") || (data[i].entity_category === "W" && "Wholeseller") || (data[i].entity_category === "D" && "Distributer") }
//                 </td>
//                 <td>
//                     ${ (data[i].entity_type === "pvtltd" && "Private Limited") || (data[i].entity_type === "llp" && "Limited Liablity Partnership") || (data[i].entity_type === "part" && "Partnership") || (data[i].entity_type === "prop" && "Propertieship")}
//                 </td>
//                 <td>
//                     ${ data[i].is_gst_enrolled  ? "Yes" : "No" }
//                 </td>
//                 <td>
//                     ${ data[i].is_active ? "Yes" : "No" }
//                 </td>
//                 <td style="text-transform: capitalize;
//                 ">${data[i].status.replace(/_/g," ")}</td>
//                 <td><a class="btn btn-sm btn-info btn-sm" href="/v1/reviewer/customer/${data[i].id}">View</a></td>
//             </tr>
//         `;
//         tbody += child
//     }
//     table_body.innerHTML = tbody
// }

// It is used to load data inside a table End

