var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function remove_protocol(url) {
    return url.replace(/(^\w+:|^)\/\//, '');
}

$(document).ajaxStart($.blockUI).ajaxStop($.unblockUI);

$(document).ready(function () {
    let true_icon = '<i class="material-icons" style="color: green">check</i>';
    let false_icon = '<i class="material-icons" style="color: red">close</i>';
    var table = $('#candidate_urls_table').DataTable({
        "scrollY": true,
        "serverSide": true,
        "stateSave": true,
        "ajax": `/api/candidate-urls/?format=datatables&collection_id=${collection_id}`,
        "columns": [
            {
                "data": "url", "render": function (data, type, row) {
                    return `<a target="_blank" href="${data}" data-url="/api/candidate-urls/${data['id']}/" class="url_link"> <i class="material-icons">open_in_new</i></a> ${data.replace(/(^\w+:|^)\/\//, '')}`;
                }
            },
            {
                "data": "excluded", "class": "col-1 text-center", "render": function (data, type, row) {
                    return (data === true) ? true_icon : `<a href="#" class="exclude_individual_url" value=${remove_protocol(row['url'])}>${false_icon}</a>`;
                }
            },
            { "data": "scraped_title" },
            { "data": "generated_title" },
            {
                "data": "visited", "class": "col-1 text-center", "render": function (data, type, row) {
                    return (data === true) ? true_icon : false_icon;
                }
            },
        ],
        "createdRow": function (row, data, dataIndex) {
            if (data['excluded']) {
                $(row).addClass('table-danger');
            }
        }
    });
});

$('#test_url').text($('#test_url').text().replace(/(^\w+:|^)\/\//, ''));



// Function to get the value of a GET parameter by its name
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return "";
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

$("#excluded_bool").on("click", function () {
    if ($(this).prop("checked")) {
        // Get the current URL
        var url = window.location.href;

        // Add a GET parameter
        var is_excluded_parameter = { is_excluded: false }; // Object containing the parameter and its value
        var serialized_param = $.param(is_excluded_parameter); // Serialize the object into a query string
        var new_url = url + (url.indexOf('?') !== -1 ? '&' : '?') + serialized_param; // Append the query string to the URL

        console.log(new_url);

        // Redirect to the new URL
        window.location.href = new_url;
    } else {
        // Get the current URL
        var url = window.location.href;

        var search_params = new URLSearchParams(url.search); // Get the search parameters
        var parameter_to_remove = 'is_excluded'; // Parameter to remove
        search_params.delete(parameter_to_remove); // Remove the parameter
        url.search = search_params.toString(); // Update the search part of the URL
        var new_url = url.toString(); // Get the modified URL

        // Redirect to the new URL
        window.location.href = new_url;
    };
});



$("#excluded_bool").on("click", function () {
    if ($(this).prop("checked")) {
        $("#excluded").val("True");
    } else {
        $("#excluded").val("False");
    };
});

$("#visited_bool").on("click", function () {
    if ($(this).prop("checked")) {
        $("#visited").val("True");
    } else {
        $("#visited").val("False");
    };
});

$(".url_part_button").on("click", function () {
    $.post('/api/exclude-patterns/', {
        collection: collection_id,
        match_pattern: $(this).attr("value"),
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        console.log(response);
        window.location.reload();
    });
});

function exclude_individual_url(url) {
    $.post('/api/exclude-patterns/', {
        collection: collection_id,
        match_pattern: url,
        pattern_type: 1, // individual_url
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        console.log(response);
        window.location.reload();
    });
}

$("body").on("click", '.exclude_individual_url', function () {
    exclude_individual_url($(this).attr("value"));
});



function add_exclude_pattern(pattern) {
    let input = $(
        `
            <div class="row pattern_row">
                <div class="col-8">
                    <input class="form-control" value="${pattern}*" />
                </div>
                <div class="col">
                    <button type="button" class="btn btn-danger btn-sm delete_input" hx-delete="/exclude-pattern" hx-confirm="Are you sure you wish to delete this pattern?">x</button>
                </div>
            </div>
        `
    );
    $('#exclude_patterns').append(input);
}

$('#add_exclude_pattern').on('click', function () {
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
});

$("body").on("click", ".delete_input", function () {
    $(this).parents(".pattern_row").remove();
    window.location.reload();
    // $.delete('/api/exclude-patterns/', {
    //     collection: '85',
    //     match_pattern: $(this).attr("value"),
    //     csrfmiddlewaretoken: csrftoken
    // }, function (response) {
    //     console.log(response);
    //     window.location.reload();
    // });
});

$("body").on("click", ".add_new_pattern", function () {
    let pattern = $(this).parents(".pattern_row").find("input").val();
    $.post('/api/exclude-patterns/', {
        collection: collection_id,
        match_pattern: pattern,
        csrfmiddlewaretoken: csrftoken
    }, function (response) {
        console.log(response);
        window.location.reload();
    });
});

$(".new-title").on("change", function () {
    let title = $(this).val();
    let url = $(this).attr("data-url");
    $.ajax({
        url: url,
        type: "POST",
        data: {
            title: title,
            csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
        },
        success: function (data) {
            console.log(data);
        },
    });
});

$("body").on("click", ".url_link", function (event) {
    let url = $(this).attr("data-url");
    let $mylink = $(this);
    console.log(url);
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
            $mylink.closest('tr').find('.text-center i').css('color', 'green').text('done');
        },
    });
    return true;
});
