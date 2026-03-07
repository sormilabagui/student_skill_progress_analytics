document.addEventListener("DOMContentLoaded", function () {

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

});