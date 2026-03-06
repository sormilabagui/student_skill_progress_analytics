const ctx = document.getElementById('skillsPieChart');

new Chart(ctx,{
type:'pie',
data:{
labels:['Programming','Aptitude','Core CS','Tools'],
datasets:[{
data:[45,25,20,10]
}]},
options:{
    responsive: true,
    maintainAspectRatio: false
}
});