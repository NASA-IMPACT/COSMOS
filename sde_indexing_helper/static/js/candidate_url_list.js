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
    add_exclude_pattern($(this).attr("value"));
});

function add_exclude_pattern(pattern) {
    let input = $(
        `
            <div class="row pattern_row">
                <div class="col-8">
                    <input class="form-control" value="${pattern}*" />
                </div>
                <div class="col">
                    <button type="button" class="btn btn-danger btn-sm delete_input">x</button>
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
                    <button type="button" class="btn btn-danger btn-sm delete_input">x</button>
                </div>
            </div>
        `
    );
    $('#exclude_patterns').append(input);
});

$("body").on("click", ".delete_input", function () {
    console.log("here");
    $(this).parents(".pattern_row").remove();
});
