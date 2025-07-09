document.addEventListener('DOMContentLoaded', function() {
    const forms = document.getElementsByTagName('form');
    for (let form of forms) {
        form.addEventListener('submit', function(e) {
            alert('Data makanan telah disimpan!');
        });
    }
});
