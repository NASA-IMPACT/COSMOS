let ctx = document.getElementById("chart").getContext("2d");


const labels = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
"November", "December"
];
const data = {
  labels: labels,
  datasets: [{
    label: 'Total SDE Entries',
    data: [65, 59, 80, 81, 56, 55, 40, 43,7,50,12,52],
    fill: true,
    borderColor: '#65B1EF',
    tension: 0.1
  }]
};

const stackedLine = new Chart(ctx, {
    type: 'line',
    data: data,
    options: {
   
        plugins: {
         
            title: {
                display: true,
                text: 'Total SDE Entries 3000',
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
                   color:'#A7BACD'
                }
            }
        }
    }
});


