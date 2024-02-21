$(document).ready(function () {
    let table = $('#url_counts_table').DataTable({
        initComplete: function (settings, json) {
            // calculate the sum when table is first created:
            doSum();
        },
        "paging": false,
        "stateSave": true,
        "fixedHeader": true,
    });

    $('#url_counts_table').on('draw.dt', function () {
        // re-calculate the sum whenever the table is re-displayed:
        doSum();
    });

    // This provides the sum of all records:
    function doSum() {
        // get the DataTables API object:
        var table = $('#url_counts_table').DataTable();
        // set up the initial (unsummed) data array for the footer row:
        var totals = ['Totals', '', 0, 0, 0, 0];
        // iterate all rows - use table.rows( {search: 'applied'} ).data()
        // if you want to sum only filtered (visible) rows:
        totals = table.rows().data()
            // sum the amounts:
            .reduce(function (sum, record) {
                for (let i = 2; i <= 8; i++) {
                    sum[i] = sum[i] + numberFromString(record[i]);
                }
                return sum;
            }, totals);
        // place the sum in the relevant footer cell:
        for (let i = 1; i <= 8; i++) {
            var column = table.column(i);
            $(column.footer()).html(formatNumber(totals[i]));
        }
    }

    function numberFromString(s) {
        // Check if the input is a string
        if (typeof s === 'string') {
            // Create a temporary div element
            var tempDiv = document.createElement('div');
            // Set the inner HTML of the div to the input string
            tempDiv.innerHTML = s;
            // Extract the text content from the div
            var text = tempDiv.textContent || tempDiv.innerText || "";

            // Remove any non-numeric characters (except for the decimal point)
            return text.replace(/[^\d.-]/g, '') * 1;
        } else if (typeof s === 'number') {
            // If it's already a number, return it as is
            return s;
        } else {
            // If the input is neither a string nor a number, return 0
            return 0;
        }
    }

    function formatNumber(n) {
        return n.toLocaleString(); // or whatever you prefer here
    }

});

// let table = $('#url_counts_table').DataTable({
// "paging": false,
// "stateSave": true,
// "fixedHeader": true,
//     initComplete: function (settings, json) {
//         // calculate the sum when table is first created:
//         doSum();
//     }

//     $('#url_counts_table').on('draw.dt', function () {
//         // re-calculate the sum whenever the table is re-displayed:
//         doSum();
//     })


//     // "footerCallback": function (row, data, start, end, display) {
//     //     var api = this.api();

//     //     // Calculate the total for the first column in the displayed data
//     //     var total = api
//     //         .column(2, { page: 'current' })
//     //         .data()
//     //         .reduce(function (a, b) {
//     //             return a + b;
//     //         }, 0);

//     //     // Update the footer
//     //     $(api.column(2).footer()).html(total);
//     //     $(api.column(3).footer()).html(total);
//     //     $(api.column(4).footer()).html(total);
//     //     $(api.column(5).footer()).html(total);
//     // }
// });
