document.getElementById('imageForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent form from reloading the page

    const formData = new FormData();
    const imageFile = document.getElementById('imageUpload').files[0];

    if (imageFile) {
        formData.append("image", imageFile);

        try {
            // Send POST request to the backend
            const response = await fetch('http://127.0.0.1:5000/predict_food', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('foodName').textContent = data.food_name;
                document.getElementById('result').classList.remove('hidden');
            } else {
                throw new Error('Failed to fetch the food name.');
            }
        } catch (error) {
            alert("Error: " + error.message);
        }
    } else {
        alert("Please select an image.");
    }
});
