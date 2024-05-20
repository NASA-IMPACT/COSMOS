let originalValue = document.getElementById('github-link-display').textContent;
document.getElementById('github-link-form').style.display = 'none';
document.getElementById('cancel-github-link-button').style.display = 'none';
document.getElementById('edit-github-link-button').addEventListener('click', function() {
    document.getElementById('id_github_issue_link').value = originalValue;
    document.getElementById('cancel-github-link-button').style.display = 'block';
    document.getElementById('edit-github-link-button').style.display = 'none';
    document.getElementById('github-link-display').style.display = 'none';
    document.getElementById('github-link-form').style.display = 'block';
});

document.getElementById('cancel-github-link-button').addEventListener('click', function() {
    document.getElementById('cancel-github-link-button').style.display = 'none';
    document.getElementById('edit-github-link-button').style.display = 'block';
    document.getElementById('github-link-display').style.display = 'block';
    document.getElementById('github-link-form').style.display = 'none';
    document.getElementById('id_github_issue_link').value = originalValue;
});

  $(document).ready(function () {
    $("body").on("change", "#detailDivisionDropdown", function () {
        var collection_id = $(this).data('collection-id');
       postDivisionChange(collection_id,$(this).val());
    });

    $("body").on("change", "#detailDocTypeDropdown", function () {
        var collection_id = $(this).data('collection-id');
        var collection_division = $(this).data('collection-division');
        postDocTypeChange(collection_id,$(this).val());
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
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
            toastr.success('Division Updated!');
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
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
            toastr.success('Document Type Updated!');
        },
    });
}
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
        toastr.success("Workflow Status Updated!");
      },
    });
  }

function handleWorkflowStatusSelect() {
    $("body").on("click", ".workflow_status_select", function () {
      var collection_id = $(this).data("collection-id");
      var workflow_status = $(this).attr("value");
      var workflow_status_text = $(this).text();
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

      $button.text(workflow_status_text);
      $button.removeClass(
        "btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary"
      );
      $button.addClass(color_choices[parseInt(workflow_status)]);
      postWorkflowStatus(collection_id, workflow_status);
    });
  }

  $(document).ready(function () {
    handleWorkflowStatusSelect();
  });