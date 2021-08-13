const subCategoryList = document.querySelector(".sub_category-list");
const subCategoryInput = document.querySelector("#sub_categories");
var categoryName = document.getElementById("category-name");
var categoryImg = document.getElementById("category-img");
const categoryForm = document.getElementById("catgeory-form");
var subCategoryData = [];
var activeItem = null;
var categoryId = null;
var form_data = new FormData();


const updateUrl = window.location.href;

if (updateUrl.includes("update")) {
  categoryId = updateUrl
    .slice(updateUrl.slice(0, updateUrl.lastIndexOf("/")).lastIndexOf("/") + 1)
    .replace("/", "");
  fetch(`/v1/seller/inventory/categories/${categoryId}/`)
    .then((res) => res.json())
    .then((data) => {
      categoryName.value = data.name;
      subCategoryData = [...data.sub_categories];
      showSubCategoryUpdate(subCategoryData);
      let list = new DataTransfer();
      let file = new File(["content"], data.image);
      list.items.add(file);
      let myFileList = list.files;
      categoryImg.files = myFileList
    })
    .catch((err) => console.log(err));
} else {
  console.log("hello world");
}

subCategoryInput.addEventListener("change", function (e) {
  if (activeItem != null) {
    subCategoryData[activeItem].name = e.target.value;
    subCategoryList.children[activeItem].children[0].children[0].innerHTML =
      e.target.value;
    activeItem = null;
  } else {
    subCategoryData.push({ name: e.target.value });
    showSubCategory(subCategoryData);
  }
  subCategoryInput.value = "";
});

categoryImg.addEventListener("change",function(e){
    form_data.append("image", categoryImg.files[0]);
})

categoryForm.addEventListener("submit", function (event) {
  event.preventDefault();
  if(categoryId){
    form_data.append("id", categoryId);
    url = `/v1/seller/inventory/categories/${categoryId}/`;
  }else{
    url = "/v1/seller/inventory/categories/";
  }
  form_data.append("name", categoryName.value);
  form_data.append("sub_categories", JSON.stringify(subCategoryData));
  const alertBox = document.getElementById("alert-box")
  fetch(url, {
    method: "POST",
    body: form_data,
  })
    .then((res) => res.json())
    .then((data) => {
        alertBox.style.display = "block";
        setTimeout(() => {
            window.location.href = "/v1/reviewer/categories/";
        },4000)
    })
    .catch((error) => console.log(error));
});

function showSubCategory(subCategory) {
  const subCategoryDiv = document.createElement("div");
  subCategoryDiv.classList.add("shadow-lg");
  subCategoryDiv.setAttribute("id", "subcategory-div");
  const subCategoryItem = document.createElement("li");
  subCategoryItem.classList.add(
    "list-group-item",
    "p-2",
    "border-top",
    "d-flex",
    "justify-content-between",
    "align-items-center"
  );

  for (var i = 0; i < subCategory.length; i++) {
    subCategoryItem.innerHTML = `<span>${subCategory[i].name}</span> 
        <div class="flex justify-content-center align-items-center">
                <span class="ni ni-ruler-pencil edit-subcategory" onclick="editSubcategory(${i})"  style="cursor:pointer;"></span>
                <span class="ni ni-fat-remove" onclick="deleteSubcategory(${i})" style="cursor:pointer;"></span>
        </div>`;
    subCategoryDiv.appendChild(subCategoryItem);
    subCategoryDiv.setAttribute("data-id", i);
  }
  subCategoryList.appendChild(subCategoryDiv);
}

function editSubcategory(i) {
  subCategoryInput.setAttribute("data-item", i);
  subCategoryInput.value = subCategoryData[i].name;
  activeItem = i;
}

function deleteSubcategory(i) {
  subCategoryData.pop(i);
  activeItem = null
  if (subCategoryList.children.length === 1) {
    subCategoryList.children[0].remove();
  } else {
    subCategoryList.children[i].remove();
  }
}


function showSubCategoryUpdate(subCategory) {
  let subCategoryContent = ``;
  for (var i = 0; i < subCategory.length; i++) {
    subCategoryContent += `
            <div class="shadow-lg" id="subcategory-div">
                <li class="list-group-item p-2 border-top d-flex justify-content-between align-items-center">
                    <span>${subCategory[i].name}</span> 
                    <div class="flex justify-content-center align-items-center">
                            <span class="ni ni-ruler-pencil edit-subcategory" onclick="editSubcategory(${i})"  style="cursor:pointer;"></span>
                            <span class="ni ni-fat-remove" onclick="deleteSubcategory(${i})" style="cursor:pointer;"></span>
                    </div>
                </li>
            </div>
        `;
  }
  subCategoryList.innerHTML = subCategoryContent;
}
