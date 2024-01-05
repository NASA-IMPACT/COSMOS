let table = $('#consolidation_table').DataTable({
    "paging": false,
    "stateSave": true,
    "dom": 'Pfritip',
    searchPanes: {
        viewTotal: true,
        columns: [1]
    }
});
