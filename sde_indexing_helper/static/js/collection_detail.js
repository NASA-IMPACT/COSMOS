var collection_id;
var newDivisionVal;
var currentDivisionVal;
var currentDivisonText;
var editTitleModal; // boolean value to confirm if the edit title modal is active

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
  collection_id = $("#detailDocTypeDropdown").data("collection-id");
});

$(document).ready(function () {
  $("body").on("change", "#detailDivisionDropdown", function () {
    $modal = $("#areYouSureModal").modal();
    var selectedText = $("#detailDivisionDropdown option:selected").text();
    $(".modal-title").text("Are you sure?");
    $("#caption").text(
      `Divison will be changed from ${currentDivisonText} to ${selectedText}.`
    );
    $("#makeChangeButton").text(`Yes`);
    $("#dontMakeChangeButton").text(`No`);
    collection_id = $(this).data("collection-id");
    newDivisionVal = $(this).val();
  });

  $("body").on("change", "#detailDocTypeDropdown", function () {
    postDocTypeChange(collection_id, $(this).val());
  });
});

$(document).ready(function () {
  $("body").on("click", ".editTitle", function () {
    $modal = $("#areYouSureModal").modal();
    editTitleModal = true;
    $(".modal-title").text("Rename Page Title");
    $("#caption").text(`New name for Landing Page`);
  });
  $("#makeChangeButton").text(`Rename`);
  $("#dontMakeChangeButton").text(`Cancel`);
  var inputField = $(
    '<input type="text" name="inputFieldName" id="inputFieldId">'
  );
  $("#modalForm").prepend(inputField);
});

$(document).ready(function () {
  $("form").on("click", "button", function (event) {
    event.preventDefault();
    var buttonId = $(this).attr("id");

    if (editTitleModal) {
      var inputValue = $("#inputFieldId").val();
      if (buttonId === "makeChangeButton") {
        patchTitle(collection_id, inputValue);
      } else if (buttonId === "dontMakeChangeButton") {
        $modal = $("#areYouSureModal").modal("hide");
      }
    } else {
      if (buttonId === "makeChangeButton") {
        postDivisionChange(collection_id, newDivisionVal);
      } else if (buttonId === "dontMakeChangeButton") {
        $("#detailDivisionDropdown").val(currentDivisionVal);
        $modal = $("#areYouSureModal").modal("hide");
      }
    }
  });
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function patchTitle(collection_id, inputValue) {
  $.ajax({
    url: "/api/collections/" + collection_id + "/",
    type: "PATCH",
    data: {
      name: inputValue,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      console.log("Success:", data);
      toastr.success("Name Updated!");
    },
    error: function (xhr, textStatus, errorThrown) {
      console.log("Error:", errorThrown);
      toastr.error("Error updating name.");
    },
  });
}

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
