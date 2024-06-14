var collection_id;
var newDivisionVal;
var currentDivisionVal;
var currentDivisonText;
var currentUrlToDelete;

let table = $("#workflow_history_table").DataTable({ 
  paging: false,
  stateSave: false,
  orderCellsTop: false,
  fixedHeader: false,
  searching:false,
  order: []
});

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

$(document).ready(function () {
  $("body").on("change", "#detailDocTypeDropdown", function () {
    postDocTypeChange(collection_id, $(this).val());
  });
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

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

// Toast for changing workflow status
$(document).ready(function () {
  if (localStorage.getItem("WorkflowStatusChange")) {
    toastr.success("Workflow Status Updated!");
    localStorage.removeItem("WorkflowStatusChange");
  }
});

//Scroll position for comments
$(document).ready(function () {
  if (localStorage.getItem("commentScroll")) {
    $(window).scrollTop(localStorage.getItem("commentScroll"));
    localStorage.removeItem("commentScroll");
  }
});

//////////////////////////////
///// DELETE URL CHANGE //////
//////////////////////////////

function handleDeleteURLButtonClick(dataId, dataURL) {
  $modal = $("#deleteURLModal").modal();
  $(".delete-URL-caption").text(`Are you sure you want to delete ${dataURL}?`);
  $("#deleteURLModal").on("keydown", function (event) {
    if (event.keyCode === 13) {
      // Check if the focused element is the button
      if (document.activeElement.id === "deleteURLModal") {
        // Simulate a click event on the button
        $.ajax({
          url: "/delete-required-url/" + dataId,
          type: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
          },
          success: function (data) {
            window.location.reload();
          },
          error: function (xhr, textStatus, errorThrown) {
            console.log("Error:", errorThrown);
            toastr.error("Error deleting URL.");
          },
        });
      }
    }
  });

  $("#deleteURLModalForm").on("click", "button", function (event) {
    event.preventDefault();
    var buttonId = $(this).attr("id");

    if (buttonId === "cancelURLDeletion") {
      $modal = $("#deleteURLModal").modal("hide");
      return;
    } else if (buttonId === "deleteURL" && dataId === currentUrlToDelete) {
      $.ajax({
        url: "/delete-required-url/" + dataId,
        type: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        success: function (data) {
          window.location.reload();
        },
        error: function (xhr, textStatus, errorThrown) {
          console.log("Error:", errorThrown);
          toastr.error("Error deleting URL.");
        },
      });
    }
  });
}

$(document).ready(function () {
  $("body").on("click", ".urlDeleteButton", function (e) {
    e.preventDefault();
    var dataId = $(this).data("id");
    currentUrlToDelete = dataId.id;
    handleDeleteURLButtonClick(dataId.id, dataId.url);
  });
});

//////////////////////////////
///// DIVISION CHANGE ////////
//////////////////////////////

$(document).ready(function () {
  $("body").on("change", "#detailDivisionDropdown", function () {
    $modal = $("#divisionChangeModal").modal();
    var selectedText = $("#detailDivisionDropdown option:selected").text();
    $("#caption").html(
      `Divison will be changed from <span class="bold">${currentDivisonText}</span> to <span class="bold">${selectedText}</span>.`
    );
    collection_id = $(this).data("collection-id");
    newDivisionVal = $(this).val();
  });

  $("#divisionChangeModalForm").on("click", "button", function (event) {
    event.preventDefault();
    var buttonId = $(this).attr("id");

    switch (buttonId) {
      case "makeDivisionChange":
        currentDivisionVal = $("#detailDivisionDropdown").val();
        postDivisionChange(collection_id, newDivisionVal);
        break;
      case "cancelDivisionChange":
        $("#detailDivisionDropdown").val(currentDivisionVal);
        $modal = $("#divisionChangeModal").modal("hide");
        break;
    }
  });
});

// store current division option
$(document).ready(function () {
  currentDivisionVal = $("#detailDivisionDropdown").val();
  currentDivisonText = $("#detailDivisionDropdown option:selected").text();
  collection_id = $("#detailDocTypeDropdown").data("collection-id");
});

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
      currentDivisionVal = $("#detailDivisionDropdown").val();
      currentDivisonText = $("#detailDivisionDropdown option:selected").text();
    },
    error: function (xhr, textStatus, errorThrown) {
      // console.log("Error:", errorThrown);
      toastr.error("Error updating name.");
    },
  });
}

// on close of modal, manually resetting division value to original value
$(document).ready(function () {
  $("#closeDivisionModal").on("click", function (event) {
    event.preventDefault();
    $("#detailDivisionDropdown").val(currentDivisionVal);
    $("#divisionChangeModal").modal("hide");
  });
});

// Close the modal when clicking outside of the modal content
$(document).ready(function () {
  $(window).click(function (event) {
    if ($(event.target).is("#divisionChangeModal")) {
      $("#detailDivisionDropdown").val(currentDivisionVal);
      $modal = $("#divisionChangeModal").modal("hide");
    }
  });
});

//////////////////////////////
/////// TITLE CHANGE ////////
//////////////////////////////

$(document).ready(function () {
  $(".editTitle").on("click", function () {
    $modal = $("#titleChangeModal").modal();
    var currentName = $("#collectionName").text();
    $("#titleCaption").text(`Name will be changed from ${currentName} to: `);
  });
});

$(document).ready(function () {
  $("#closeTitleModal").on("click", function (event) {
    event.preventDefault();
    $("#titleChangeModal").modal("hide");
  });
});

$(document).ready(function () {
  $(window).click(function (event) {
    if ($(event.target).is("#titleChangeModal")) {
      $modal = $("#titleChangeModal").modal("hide");
    }
  });
});

function patchTitle(collection_id, inputValue) {
  $.ajax({
    url: "/api/collections/" + collection_id + "/",
    type: "PUT",
    data: {
      name: inputValue,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      // console.log("Success:", data);
      $(".collectionName").text(`${data.name}`);
      toastr.success("Name Updated!");
    },
    error: function (xhr, textStatus, errorThrown) {
      // console.log("Error:", errorThrown);
      toastr.error("Error updating name.");
    },
  });
}

$(document).ready(function () {
  $("#titleChangeModalForm").on("click", "button", function (event) {
    event.preventDefault();
    var buttonId = $(this).attr("id");

    switch (buttonId) {
      case "renameTitle":
        var inputValue = $("#inputFieldId").val();
        patchTitle(collection_id, inputValue);
        break;
      case "cancelTitleRename":
        editTitleModal = false;
        $modal = $("#titleChangeModal").modal("hide");
        break;
    }
  });
});

$(document).ready(function () {
  $("#inputFieldId").on("keypress", function (event) {
    if (event.which === 13) {
      event.preventDefault();
      var inputValue = $(this).val();
      if (inputValue.trim() !== "") {
        patchTitle(collection_id, inputValue);
        $modal = $("#titleChangeModal").modal("hide");
      } else return;
    }
  });
});

const $timeline = $("#timeline");

function checkArrows() {
  const scrollLeft = $timeline.scrollLeft();
  const maxScrollLeft = $timeline[0].scrollWidth - $timeline[0].clientWidth;

  if (scrollLeft === 0) {
    $("#left-arrow").hide();
  } else {
    $("#left-arrow").show();
  }

  if (scrollLeft >= maxScrollLeft) {
    $("#right-arrow").hide();
  } else {
    $("#right-arrow").show();
  }
}

// Clicking on left right arrows to move timeline
$(document).ready(function () {
  $("#left-arrow").click(function () {
    $("#timeline").scrollLeft($("#timeline").scrollLeft() - 510);
    checkArrows();
  });

  $("#right-arrow").click(function () {
    $("#timeline").scrollLeft($("#timeline").scrollLeft() + 510);
    checkArrows();
  });
});

$timeline.on("scroll", checkArrows);

// Scroll to center the highlighted cell
function centerHighlighted() {
  const $timeline = $("#timeline");
  const $highlighted = $timeline.find(".highlight");

  if ($highlighted.length) {
    const timelineWidth = $timeline.width();
    const highlightedOffset =
      $highlighted.offset().left - $timeline.offset().left;
    const highlightedWidth = $highlighted.outerWidth(true);
    const scrollLeft = $timeline.scrollLeft();
    const centerPosition =
      highlightedOffset - timelineWidth / 2 + highlightedWidth / 2;

    $timeline.scrollLeft(scrollLeft + centerPosition);
  }
}

centerHighlighted();

function postWorkflowStatus(collection_id, workflow_status) {
  var url = `/api/collections/${collection_id}/`;
  $.ajax({
    url: url,
    type: "PUT",
    data: {
      workflow_status: workflow_status,
      csrfmiddlewaretoken: csrftoken,
    },
    headers: {
      "X-CSRFToken": csrftoken,
    },
    success: function (data) {
      localStorage.setItem("WorkflowStatusChange", data.OperationStatus);
      location.reload();
    },
  });
}

function handleWorkflowStatusSelect() {
  $("body").on("click", ".workflow_status_select", function () {
    $("#workflowStatusChangeModal").modal();
    var collectionName = $("#collectionName").text();
    var collection_id = $(this).data("collection-id");
    var workflow_status = $(this).attr("value");
    var new_workflow_status = $(this).text();

    $(".workflow-status-change-caption").text(
      `Workflow status for ${collectionName} will change to ${new_workflow_status}`
    );

    $("#workflowStatusChangeModalForm").on("click", "button", function (event) {
      event.preventDefault();
      var buttonId = $(this).attr("id");

      switch (buttonId) {
        case "cancelworkflowStatusChange":
          $("#workflowStatusChangeModal").modal("hide");
          break;
        case "changeWorkflowStatus":
          var color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
            8: "btn-secondary",
            9: "btn-light",
            10: "btn-danger",
            11: "btn-warning",
            12: "btn-info",
            13: "btn-success",
            14: "btn-primary",
            15: "btn-info",
            16: "btn-secondary",
          };

          $button = $(`#workflow-status-button-${collection_id}`);

          $button.text(new_workflow_status);
          $button.removeClass(
            "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
          );
          $button.addClass(color_choices[parseInt(workflow_status)]);
          postWorkflowStatus(collection_id, workflow_status);
          $("#workflowStatusChangeModal").modal("hide");
          break;
      }
    });
  });
}

$(document).ready(function () {
  handleWorkflowStatusSelect();
  $("button[name='comment_button']").click(function () {
    localStorage.setItem("commentScroll", $(window).scrollTop());
  });
});








