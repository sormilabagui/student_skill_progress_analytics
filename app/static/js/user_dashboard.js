document.addEventListener("DOMContentLoaded", function () {

    // Skill Progress Chart
    const skillCanvas = document.getElementById("skillChart");

    const labels = JSON.parse(skillCanvas.dataset.labels);
    const progress = JSON.parse(skillCanvas.dataset.progress);

    new Chart(skillCanvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Skill Progress (%)",
                data: progress,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });



    // Category Pie Chart
    const categoryCanvas = document.getElementById("categoryChart");

    const categoryLabels = JSON.parse(categoryCanvas.dataset.labels);
    const categoryValues = JSON.parse(categoryCanvas.dataset.values);

    new Chart(categoryCanvas, {
        type: "pie",
        data: {
            labels: categoryLabels,
            datasets: [{
                data: categoryValues
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });



    // Weekly Target Chart
    const weeklyCanvas = document.getElementById("weeklyChart");

    const weeklyLabels = JSON.parse(weeklyCanvas.dataset.labels);
    const weeklyData = JSON.parse(weeklyCanvas.dataset.data);

    new Chart(weeklyCanvas, {
        type: "bar",
        data: {
            labels: weeklyLabels,
            datasets: [{
                label: "Target Hours",
                data: weeklyData
            }]
        },
        options: {
            responsive: true
        }
    });

});