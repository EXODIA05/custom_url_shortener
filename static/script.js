// Wait for the document to completely load
document.addEventListener('DOMContentLoaded', () => {
    const errorBox = document.getElementById('errorBox');
    
    // If the error element exists in the HTML, add the click listener
    if (errorBox) {
        errorBox.addEventListener('click', () => {
            // Toggles the class that triggers the CSS drop-down animation
            errorBox.classList.toggle('active');
        });
    }
});