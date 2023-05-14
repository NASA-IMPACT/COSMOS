// CSRF token and collection_id
var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
var collection_id = getCollectionId();

$(document).ready(function () {
    handleAjaxStartAndStop();
    initializeDataTable();
    setupClickHandlers();
});

function handleAjaxStartAndStop() {
    $(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);
}

function initializeDataTable() {
    let true_icon = '<i class="material-icons" style="color: green">check</i>';
    let false_icon = '<i class="material-icons" style="color: red">close</i>';

    let table = $('#candidate_urls_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "stateSave": true,
        "ajax": `/api/candidate-urls/?format=datatables&collection_id=${collection_id}`,
        "columns": [
            getURLColumn(),
            getExcludedColumn(true_icon, false_icon),
            { "data": "scraped_title" },
            { "data": "generated_title" },
            getVisitedColumn(true_icon, false_icon),
            { "data": "id", "visible": false, "searchable": false },
        ],
        "createdRow": function (row, data, dataIndex) {
            if (data['excluded']) {
                $(row).addClass('table-danger');
            }
        }
    });
}

function setupClickHandlers() {
    handleExcludedBool();
    handleVisitedBool();
    handleUrlPartButton();
    handleExcludeIndividualUrlClick();
    handleAddExcludePatternClick();
    handleDeleteInputClick();
    handleAddNewPatternClick();
    handleNewTitleChange();
    handleUrlLinkClick();
}

function getURLColumn() {
    return {
        "data": "url", "render": function (data, type, row) {
            return `<a target="_blank" href="${data}" data-url="/api/candidate-urls/${row['id']}/" class="url_link"> <i class="material-icons">open_in_new</i></a> ${remove_protocol(data)}`;
        }
    }
}

function getExcludedColumn(true_icon, false_icon) {
    return {
        "data": "excluded", "class": "col-1 text-center", "render": function (data, type, row) {
            return (data === true) ? true_icon : `<a href="#" class="exclude_individual_url" value=${remove_protocol(row['url'])}>${false_icon}</a>`;
        }
    }
}

function getVisitedColumn(true_icon, false_icon) {
    true_icon = '<i class="material-icons visited_icon" style="color: green">check</i>';
    false_icon = '<i class="material-icons visited_icon" style="color: red">close</i>';
    return {
        "data": "visited", "class": "col-1 text-center", "render": function (data, type, row) {
            return (data === true) ? true_icon : false_icon;
        }
    }
}

function handleExcludedBool() {
    $("#excluded_bool").on("click", function () {
        var newValue = $(this).prop("checked") ? "True" : "False";
        $("#excluded").val(newValue);
        updateUrlWithExclusion(newValue);
    });
}

function handleVisitedBool() {
    $("#visited_bool").on("click", function () {
        var newValue = $(this).prop("checked") ? "True" : "False";
        $("#visited").val(newValue);
    });
}

function handleUrlPartButton() {
    $(".url_part_button").on("click", function () {
        postExcludePatterns($(this).attr("value"));
    });
}

function handleExcludeIndividualUrlClick() {
    $("body").on("click", '.exclude_individual_url', function () {
        postExcludePatterns(match_pattern = $(this).attr("value"), pattern_type = 1);
    });
}

function handleAddExcludePatternClick() {
    $('#add_exclude_pattern').on('click', function () {
        add_exclude_pattern();
    });
}

function handleDeleteInputClick() {
    $("body").on("click", ".delete_input", function () {
        $(this).parents(".pattern_row").remove();
        window.location.reload();
    });
}

function handleAddNewPatternClick() {
    $("body").on("click", ".add_new_pattern", function () {
        let pattern = $(this).parents(".pattern_row").find("input").val();
        postExcludePatterns(pattern);
    });
}

function handleNewTitleChange() {
    $(".new-title").on("change", function () {
        let title = $(this).val();
        let url = $(this).attr("data-url");
        postNewTitle(url, title);
    });
}

function handleUrlLinkClick() {
    $("body").on("click", ".url_link", function (event) {
        let url = $(this).attr("data-url");
        postVisited(url);
        $(this).closest('tr').find('.visited_icon').css('color', 'green').text('done');
    });
}

function postExcludePatterns(match_pattern, pattern_type = 0) {
    $.post('/api/exclude-patterns/', {
        collection: collection_id,
        match_pattern: match_pattern,
        pattern_type: pattern_type,
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        console.log(response);
        window.location.reload();
    });
}

function postNewTitle(url, title) {
    $.ajax({
        url: url,
        type: "POST",
        data: {
            title: title,
            csrfmiddlewaretoken: csrftoken,
        },
        success: function (data) {
            console.log(data);
        },
    });
}

function postVisited(url) {
    $.ajax({
        url: url,
        type: "PUT",
        data: {
            visited: true,
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
        },
    });
}

function getCollectionId() {
    return collection_id;
}

function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return "";
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function remove_protocol(url) {
    return url.replace(/(^\w+:|^)\/\//, '');
}

function add_exclude_pattern(pattern) {
    let input = $(
        `
            <div class="row pattern_row">
                <div class="col-8">
                    <input class="form-control" />
                    </div>
                    <div class="col">
                        <button type="button" class="btn btn-success btn-sm add_new_pattern">
                            ✔
                        </button>
                    </div>
                </div>
            `
    );
    $('#exclude_patterns').append(input);
}
