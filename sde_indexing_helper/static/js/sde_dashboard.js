////////////////// Division ////////////////////////////
let divisionChart = document.getElementById("divisionChart").getContext("2d");

const labels = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
    "November", "December"
];
const divisionData = {
    labels: labels,
    datasets: [{
        label: 'Total SDE Entries',
        data: [65, 59, 80, 81, 56, 55, 40, 43, 7, 50, 12, 52],
        fill: true,
        borderColor: '#65B1EF',
        tension: 0.1
    }]
};

const stackedLine = new Chart(divisionChart, {
    type: 'line',
    data: divisionData,
    options: {

        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Total SDE Entries',
                position: 'top',
                align: 'start',
                color: '#A7BACD',
                font: {
                    family: 'sans-serif',
                    size: 14,
                    weight: '400',
                },
            },
            subtitle: {
                display: true,
                position: 'top',
                align: 'start',
                padding: 10,
                text: '3000',
                color: '#65B1EF',
                font: {
                    size: 24,
                    family: 'sans-serif',
                    weight: '700',
                },
            },
        },
        scales: {
            y: {
                stacked: true,
                grid: {
                    color: '#A7BACD'
                }
            }
        }
    }
});
/////////////////////////////////////////////
////// candidiate urls /////////////////////


let urlChart = document.getElementById("urlChart").getContext("2d");

const urlData = {
    labels: labels,
    datasets: [{
        label: 'Total Scraped URLs',
        data: [6512, 59, 800, 81, 56, 55, 40, 4300, 7, 50, 120, 520],
        fill: true,
        borderColor: '#65B1EF',
        tension: 0.1
    }]
};

const stackedLine2 = new Chart(urlChart, {
    type: 'line',
    data: urlData,
    options: {

        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Total Scraped URLs',
                position: 'top',
                align: 'start',
                color: '#A7BACD',
                font: {
                    family: 'sans-serif',
                    size: 14,
                    weight: '400',
                },
            },
            subtitle: {
                display: true,
                position: 'top',
                align: 'start',
                padding: 10,
                text: '5280',
                color: '#65B1EF',
                font: {
                    size: 24,
                    family: 'sans-serif',
                    weight: '700',
                },
            },
        },
        scales: {
            y: {
                stacked: true,
                grid: {
                    color: '#A7BACD'
                }
            }
        }
    }
});