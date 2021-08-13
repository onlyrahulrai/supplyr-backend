const subCategoryList = document.querySelector(".sub_category-list");
const subCategoryInput = document.querySelector("#sub_categories");
const categoryName = document.getElementById("category-name")
const categoryImg = document.getElementById("category-img")
const categoryForm = document.getElementById("catgeory-form");
var subCategoryData = [];
var activeItem = null

subCategoryInput.addEventListener("change", function (e) {
    if (activeItem != null){
        subCategoryData[activeItem] = e.target.value;
        subCategoryList.children[activeItem].children[0].children[0].innerHTML = e.target.value
        activeItem = null
    }else{
        subCategoryData.push({"name":e.target.value});
        showSubCategory(subCategoryData);
    }
    subCategoryInput.value = "";
});


categoryForm.addEventListener("submit", function (event) {
  event.preventDefault();
  const form_data = new FormData();
  form_data.append("name",categoryName.value)
  form_data.append("image",categoryImg.files[0])
  form_data.append("sub_categories",JSON.stringify(subCategoryData))
  url = "/v1/seller/inventory/categories/"
  fetch(url,{
    method:"POST",
    body:form_data
  }).then((res) => res.json())
  .then((data) => {
      console.log(data)
      window.location.href = "/v1/reviewer/categories/"
    })
  .catch((error) => console.log(error))
});

function showSubCategory(subCategory) {
    const subCategoryDiv = document.createElement("div");
    subCategoryDiv.classList.add("shadow-lg");
    subCategoryDiv.setAttribute("id","subcategory-div")
    const subCategoryItem = document.createElement("li");
    subCategoryItem.classList.add("list-group-item", "p-2", "border-top","d-flex","justify-content-between","align-items-center");
    
    for(var i=0;i<subCategory.length;i++){
        subCategoryItem.innerHTML = `<span>${subCategory[i].name}</span> 
        <div class="flex justify-content-center align-items-center">
                <span class="ni ni-ruler-pencil edit-subcategory" onclick="editSubcategory(${i})"  style="cursor:pointer;"></span>
                <span class="ni ni-fat-remove" onclick="deleteSubcategory(${i})" style="cursor:pointer;"></span>
        </div>`
        subCategoryDiv.appendChild(subCategoryItem);
        subCategoryDiv.setAttribute("data-id",i)
    }
    subCategoryList.appendChild(subCategoryDiv)
}

function editSubcategory(i){
    subCategoryInput.setAttribute("data-item",i)
    subCategoryInput.value = subCategoryData[i].name
    activeItem = i
}

function deleteSubcategory(i){
    subCategoryData.pop(i)
    if(subCategoryList.children.length === 1){
        subCategoryList.children[0].remove()
    }else{
        subCategoryList.children[i].remove()
    }
}




