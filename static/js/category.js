const subCategoryList = document.querySelector(".sub_category-list");
const subCategoryInput = document.querySelector("#sub_categories");
var categoryName = document.getElementById("category-name");
var categoryImg = document.getElementById("category-img");
const categoryFormButton = document.getElementById("catgeory-form-button");
var subCategoryData = [];
var activeItem = null;
var categoryId = null;
var form_data = new FormData();
var imageUrl = null;

const categoryNameValidation = document.getElementById(
  "category-name-validation"
);
const categoryImgValidation = document.getElementById(
  "category-img-validation"
);

const updateUrl = window.location.href;

if (updateUrl.includes("update")) {
  categoryId = updateUrl
    .slice(updateUrl.slice(0, updateUrl.lastIndexOf("/")).lastIndexOf("/") + 1)
    .replace("/", "");
  if (categoryId) {
    fetch(`/reviewer/categories/detail/${categoryId}/`)
      .then((res) => res.json())
      .then((data) => {
        categoryName.value = data.name;
        subCategoryData = [...data.sub_categories];
        showSubCategory(subCategoryData);
        const categoryImgField = document.getElementById("category-img-field");
        imageUrl = window.location.origin + data.image;
        const image = document.createElement("img");
        image.src = imageUrl;
        image.alt = data.name;
        image.setAttribute("width", "64px");
        image.setAttribute("height", "44px");
        categoryImgField.append(image);
        let list = new DataTransfer();
        let file = new File(["content"], data.image);
        list.items.add(file);
        let myFileList = list.files;
        categoryImg.files = myFileList;
      })
      .catch((err) => console.log(err));
  }
} else {
  console.log("hello world");
}

subCategoryInput.addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    subCategoryData.push({ name: e.target.value });
    showSubCategory(subCategoryData);
    subCategoryInput.value = "";
  }
});

// Form Validation and formData image assignment

categoryImg.addEventListener("change", function (e) {
  form_data.append("image", categoryImg.files[0]);
  categoryImgValidation.classList.add("d-none");
});

categoryName.addEventListener("keypress", function (e) {
  categoryNameValidation.classList.add("d-none");
});
// Form Validation and formData image assignment

categoryFormButton.addEventListener("click", function (event) {
  event.preventDefault();
  if (categoryName.value && categoryImg.files[0]) {
    if (categoryId) {
      form_data.append("id", categoryId);
      url = `/reviewer/categories/update/${categoryId}/`;
    } else {
      url = "/reviewer/categories/create/";
    }
    form_data.append("name", categoryName.value);
    form_data.append("sub_categories", JSON.stringify(subCategoryData));

    fetch(url, {
      method: "POST",
      body: form_data,
    })
      .then((res) => {
        const alertBox = document.getElementById("alert-box");
        alertBox.style.display = "block";
        setTimeout(() => {
          window.location.href = "/reviewer/categories/";
        }, 1000);
      })
      .catch((error) => console.log(error));
  } else {
    if (categoryImg.files[0] === undefined) {
      categoryImgValidation.classList.remove("d-none");
    }
    if (categoryName.value === "") {
      categoryNameValidation.classList.remove("d-none");
    }
  }
});

function deleteSubcategory(pos) {
  function arrayRemove(arr, pos) {
    return arr.filter((ele, index) => {
      return index != pos;
    });
  }
  subCategoryData = [...arrayRemove(subCategoryData, pos)];
  activeItem = null;
  subCategoryList.children[pos].remove();
  subCategoryList.innerHTML = "";
  showSubCategory(subCategoryData);
}

function showSubCategory(subCategory) {
  let subCategoryContent = ``;
  for (var i = 0; i < subCategory.length; i++) {
    subCategoryContent += `
            <div class="shadow-lg" id="subcategory-div${i}">
                <li class="list-group-item p-2 border-top d-flex justify-content-between align-items-center">
                    <span>${subCategory[i].name}</span> 
                    ${
                      subCategory[i].seller === null || subCategory[i].seller === undefined ?
                      `
                        <div class="flex justify-content-center align-items-center">
                          <span class="fas fa-pencil-alt edit-subcategory" onclick="editSubcategory(${i})"  style="cursor:pointer;"></span>
                          <span class="ni ni-fat-remove" onclick="deleteSubcategory(${i})" style="cursor:pointer;"></span>
                        </div>
                      `:``
                    }
                    
                </li>
            </div>
        `;
  }
  subCategoryList.innerHTML = subCategoryContent;
}

function editSubcategory(i) {
  const subcategoryDiv = document.getElementById("subcategory-div" + i);

  const subCategoryEditDiv = `
      <div id="subCategory-edit-div" class="w-100 d-flex align-items-center py-2 px-2"  style="border-left:3px solid; border-radius:5px 0 0 5px ">
        <input type="text" class="border-0 w-100" id="sub-category-edit-input" style="outline:none" onkeypress="subCategoryEditFunction()" value="${subCategoryData[i].name}">
        <span class="ni ni-fat-remove" style="cursor:pointer;" onclick="removeSubCategoryEditInput()"></span>
      </div>
    `;

  if (activeItem || activeItem === 0) {
    const subcategoryActiveDiv = document.getElementById(
      "subcategory-div" + activeItem
    );
    const selectSubCategoryEditDiv = document.getElementById(
      "subCategory-edit-div"
    );
    subcategoryActiveDiv.children[0].classList.remove("d-none");
    subcategoryActiveDiv.children[0].classList.add("d-flex");
    selectSubCategoryEditDiv.remove();

    activeItem = i;

    subcategoryDiv.children[0].classList.remove("d-flex");
    subcategoryDiv.children[0].classList.add("d-none");
    subcategoryDiv.innerHTML += subCategoryEditDiv;
  } else {
    activeItem = i;
    subcategoryDiv.children[0].classList.remove("d-flex");
    subcategoryDiv.children[0].classList.add("d-none");
    subcategoryDiv.innerHTML += subCategoryEditDiv;
  }

  const subCategoryEditInput = document.getElementById(
    "sub-category-edit-input"
  );
  subCategoryEditInput.focus();
}

function subCategoryEditFunction() {
  if (event.key === "Enter") {
    const subcategoryActiveDiv = document.getElementById(
      "subcategory-div" + activeItem
    );
    const selectSubCategoryEditDiv = document.getElementById(
      "subCategory-edit-div"
    );
    subcategoryActiveDiv.children[0].classList.remove("d-none");
    subcategoryActiveDiv.children[0].classList.add("d-flex");
    selectSubCategoryEditDiv.remove();
    subCategoryData[activeItem].name = event.target.value;
    subCategoryList.children[activeItem].children[0].children[0].innerHTML =
      event.target.value;
    activeItem = null;
  }
}

function removeSubCategoryEditInput() {
  const subcategoryActiveDiv = document.getElementById(
    "subcategory-div" + activeItem
  );
  const selectSubCategoryEditDiv = document.getElementById(
    "subCategory-edit-div"
  );
  subcategoryActiveDiv.children[0].classList.remove("d-none");
  subcategoryActiveDiv.children[0].classList.add("d-flex");
  selectSubCategoryEditDiv.remove();
  activeItem = null;
}
