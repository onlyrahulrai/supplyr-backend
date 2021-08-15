const subCategoryList = document.querySelector(".sub_category-list");
const subCategoryInput = document.querySelector("#sub_categories");
var categoryName = document.getElementById("category-name");
var categoryImg = document.getElementById("category-img");
const categoryForm = document.getElementById("catgeory-form");
var subCategoryData = [];
var activeItem = null;
var categoryId = null;
var form_data = new FormData();
var imageUrl = null




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
      showSubCategory(subCategoryData);
      const categoryImgField = document.getElementById("category-img-field")
      imageUrl = window.location.origin + data.image
      const image = document.createElement("img")
      image.src = imageUrl
      image.alt = data.name
      image.setAttribute("width","64px")
      image.setAttribute("height","44px")
      categoryImgField.append(image)
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

function editSubcategory(i) {
  subCategoryInput.setAttribute("data-item", i);
  subCategoryInput.value = subCategoryData[i].name;
  activeItem = i;
}

function deleteSubcategory(pos) {
  function arrayRemove(arr, pos) { 
    return arr.filter((ele,index)=> { 
        return index != pos; 
    });
  }
  subCategoryData = [...arrayRemove(subCategoryData,pos)]
  activeItem = null
  subCategoryList.children[pos].remove();
  subCategoryList.innerHTML = ""
  showSubCategory(subCategoryData)
}


function showSubCategory(subCategory) {
  let subCategoryContent = ``;
  for (var i = 0; i < subCategory.length; i++) {
    subCategoryContent += `
            <div class="shadow-lg" id="subcategory-div" data-id="${i}">
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


