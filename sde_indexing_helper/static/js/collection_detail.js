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
       postDivisonChange(collection_id,$(this).val());
    });

    $("body").on("change", "#detailDocTypeDropdown", function () {
        var collection_id = $(this).data('collection-id');
        var collection_division = $(this).data('collection-division');
        postDocTypeChange(collection_id,$(this).val(), collection_division);
    });
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function postDivisonChange(collection_id, division) {
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