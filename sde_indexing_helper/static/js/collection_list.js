let table = $('#collection_table').DataTable({
    "order": [[0, 'asc']],
    "paging": false,
    "dom": 'BPfritip',
    "buttons": [
        'csv',
        {
            text: 'JSON',
            action: function (e, dt, button, config) {
                var data = dt.buttons.exportData();

                $.fn.dataTable.fileSave(
                    new Blob([JSON.stringify(data)]),
                    'collections.json'
                );
            }
        },
    ],
    "columnDefs": [
        {
            target: -1,
            visible: false,
        },
        {
            target: 3,
            sortable: false,
        },
        {
            searchPanes: {
                options: [
                    {
                        label: '0 URLs',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() == 0;
                        }
                    },
                    {
                        label: '1 solo URL',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() == 1;
                        }
                    },
                    {
                        label: '1 to 100 URLs',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() <= 100 && $(rowData[4]).text() > 1;
                        }
                    },
                    {
                        label: '100 to 1,000 URLs',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() <= 1000 && $(rowData[4]).text() > 100;
                        }
                    },
                    {
                        label: '1000 to 10,000 URLs',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() <= 10000 && $(rowData[4]).text() > 1000;
                        }
                    },
                    {
                        label: '10000 to 100,000 URLs',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() <= 100000 && $(rowData[4]).text() > 10000;
                        }
                    },
                    {
                        label: 'Over 100,000 URLs',
                        value: function (rowData, rowIdx) {
                            return $(rowData[4]).text() > 100000;
                        }
                    }
                ]
            },
            targets: [4]
        },
    ]
});

var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();

function handleCurationStatusSelect() {
    $("body").on("click", ".curation_status_select", function () {
        var collection_id = $(this).data('collection-id');
        var curation_status = $(this).attr('value');
        var curation_status_text = $(this).text();
        var color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
        }
        $(`#curation-status-button-${collection_id}`).text(curation_status_text);
        $(`#curation-status-button-${collection_id}`).removeClass('btn-light btn-danger btn-warning btn-info btn-success btn-primary');
        $(`#curation-status-button-${collection_id}`).addClass(color_choices[curation_status]);

        postCurationStatus(collection_id, curation_status);
    });
}

function handleCuratorSelect() {
    $("body").on("click", ".curator_select", function () {
        var collection_id = $(this).data('collection-id');
        var curator_id = $(this).attr('value');
        var curator_text = $(this).text();

        $(`#curator-button-${collection_id}`).text(curator_text);
        $(`#curator-button-${collection_id}`).removeClass('btn-light btn-danger btn-warning btn-info btn-success btn-primary');
        $(`#curator-button-${collection_id}`).addClass('btn-success');

        postCurator(collection_id, curator_id);
    });
}

function postCurationStatus(collection_id, curation_status) {
    var url = `/api/collections/${collection_id}/`;
    $.ajax({
        url: url,
        type: "PUT",
        data: {
            curation_status: curation_status,
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
            toastr.success('Curation Status Updated!');
        },
    });
}

function postCurator(collection_id, curator_id) {
    var url = `/api/collections/${collection_id}/`;
    $.ajax({
        url: url,
        type: "PUT",
        data: {
            curated_by: curator_id,
            csrfmiddlewaretoken: csrftoken
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function (data) {
            toastr.success('Curator Updated!');
        },
    });
}

$(document).ready(function () {
    setupClickHandlers();
});

function setupClickHandlers() {
    handleCurationStatusSelect();
    handleCuratorSelect();
}
