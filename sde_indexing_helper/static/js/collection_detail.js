var collection_id;
var newDivisionVal;
var currentDivisionVal;
var currentDivisonText;

let originalValue = document.getElementById("github-link-display").textContent;
document.getElementById("github-link-form").style.display = "none";
document.getElementById("cancel-github-link-button").style.display = "none";
document
  .getElementById("edit-github-link-button")
  .addEventListener("click", function () {
    document.getElementById("id_github_issue_link").value = originalValue;
    document.getElementById("cancel-github-link-button").style.display =
      "block";
    document.getElementById("edit-github-link-button").style.display = "none";
    document.getElementById("github-link-display").style.display = "none";
    document.getElementById("github-link-form").style.display = "block";
  });

document
  .getElementById("cancel-github-link-button")
  .addEventListener("click", function () {
    document.getElementById("cancel-github-link-button").style.display = "none";
    document.getElementById("edit-github-link-button").style.display = "block";
    document.getElementById("github-link-display").style.display = "block";
    document.getElementById("github-link-form").style.display = "none";
    document.getElementById("id_github_issue_link").value = originalValue;
  });

// store current division option
$(document).ready(function () {
  currentDivisionVal = $("#detailDivisionDropdown").val();
  currentDivisonText = $("#detailDivisionDropdown option:selected").text();
});

$(document).ready(function () {
  $("body").on("change", "#detailDivisionDropdown", function () {
    $modal = $("#areYouSureModal").modal();
    var selectedText = $("#detailDivisionDropdown option:selected").text();
    $("#caption").text(
      `Divison will be changed from ${currentDivisonText} to ${selectedText}.`
    );
    collection_id = $(this).data("collection-id");
    newDivisionVal = $(this).val();
  });

  $("body").on("change", "#detailDocTypeDropdown", function () {
    var collection_id = $(this).data("collection-id");
    var collection_division = $(this).data("collection-division");
    postDocTypeChange(collection_id, $(this).val());
  });
});

$(document).ready(function () {
  $("form").on("click", "button", function (event) {
    event.preventDefault();

    var buttonId = $(this).attr("id");
    if (buttonId === "makeChangeButton") {
      postDivisionChange(collection_id, newDivisionVal);
    } else if (buttonId === "dontMakeChangeButton") {
      $("#detailDivisionDropdown").val(currentDivisionVal);
      $modal = $("#areYouSureModal").modal("hide");
    }
  });
});

$(document).ready(function () {
  $("#closeModalButton").on("click", function (event) {
    event.preventDefault();
    console.log("clicked!");
    $("#detailDivisionDropdown").val(currentDivisionVal);
    $("#areYouSureModal").modal("hide");
  });
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function postDivisionChange(collection_id, division) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      division: division,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      toastr.success("Division Updated!");
    },
  });
}

function postDocTypeChange(collection_id, docType) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      document_type: docType,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      toastr.success("Document Type Updated!");
    },
  });
}
