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


// $("#detailDivisionDropdown").on(
//     "change",
//     function () {
//         var test = '{{ collection }}';
//         console.log(test);
//          console.log($(this).attr('value'));
//         var collection_id = $(this).data('object');
//         console.log($(this).data());
//         console.log(collection_id);
//         // var workflow_status = $(this).attr('value');
//         // var workflow_status_text = $(this).text();
//         // var color_choices = {
//         //     1: "btn-light",
//         //     2: "btn-danger",
//         //     3: "btn-warning",
//         //     4: "btn-info",
//         //     5: "btn-info",
//         //     6: "btn-primary",
//         //     7: "btn-success",
//         //     8: "btn-secondary",
//         //     9: "btn-light",
//         //     10: "btn-danger",
//         //     11: "btn-warning",
//         //     12: "btn-info",
//         //     13: "btn-secondary",
//         //     14: "btn-success",
//         // }

//         // $possible_buttons = $('body').find(`[id="workflow-status-button-${collection_id}"]`);
//         // if ($possible_buttons.length > 1) {
//         //     $button = $possible_buttons[1];
//         //     $button = $($button);
//         // } else {
//         //     $button = $(`#workflow-status-button-${collection_id}`);
//         // }
//         // $button.text(workflow_status_text);
//         // $button.removeClass('btn-light btn-danger btn-warning btn-info btn-success btn-primary btn-secondary');
//         // $button.addClass(color_choices[parseInt(workflow_status)]);
//         // $('#collection_table').DataTable().searchPanes.rebuildPane(6);

//         // postWorkflowStatus(collection_id, workflow_status);


//     }
//   );

  $(document).ready(function () {
    $("body").on("change", "#detailDivisionDropdown", function () {
        var collection_id = $(this).data('collection-id');
        console.log($(this).val());
       postDivisonChange(collection_id,$(this).val());
    });

});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function postDivisonChange(collection_id, division) {
    console.log(collection_id);
    console.log(division);
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