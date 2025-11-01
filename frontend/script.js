document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const changeImageButton = document.getElementById('changeImageButton');
    const resultContainer = document.getElementById('resultContainer');
    const foodName = document.getElementById('foodName');
    const ingredientsList = document.getElementById('ingredientsList');
    const instructionsList = document.getElementById('instructionsList');

    // Event Listeners
    dropArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    uploadButton.addEventListener('click', uploadImage);
    changeImageButton.addEventListener('click', () => {
        previewContainer.style.display = 'none';
        resultContainer.style.display = 'none';
        uploadButton.style.display = 'block';
        fileInput.value = '';
    });

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            fileInput.files = files;
            handleFileSelect();
        }
    }

    // Handle file selection
    function handleFileSelect() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                previewContainer.style.display = 'block';
                // Keep the upload button visible after selecting an image
                uploadButton.style.display = 'block';
            };
            
            reader.readAsDataURL(file);
        }
    }

    // Upload image to server
    async function uploadImage() {
        if (!fileInput.files.length) {
            alert('Please select an image first');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('image', file);

        try {
            // Show loading state
            foodName.textContent = 'Identifying food...';
            resultContainer.style.display = 'block';
            ingredientsList.innerHTML = '';
            instructionsList.innerHTML = '';

            // Make the actual API call to our backend
            // Using port 5001 (port 5000 often conflicts with macOS AirPlay Receiver)
            const response = await fetch('http://127.0.0.1:5001/api/identify', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Server error' }));
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to identify food');
            }

            // Update UI with results
            foodName.textContent = data.food;

            // Populate metadata if available
            const metadataContainer = document.getElementById('recipeMetadata');
            if (data.recipe.prep_time || data.recipe.cook_time || data.recipe.servings || data.recipe.difficulty || data.recipe.cuisine) {
                metadataContainer.style.display = 'flex';

                if (data.recipe.prep_time) {
                    document.getElementById('prepTime').textContent = data.recipe.prep_time;
                }
                if (data.recipe.cook_time) {
                    document.getElementById('cookTime').textContent = data.recipe.cook_time;
                }
                if (data.recipe.servings) {
                    document.getElementById('servings').textContent = data.recipe.servings;
                }
                if (data.recipe.difficulty) {
                    document.getElementById('difficulty').textContent = data.recipe.difficulty;
                }
                if (data.recipe.cuisine) {
                    document.getElementById('cuisine').textContent = data.recipe.cuisine;
                }
            }

            // Populate ingredients
            if (data.recipe.ingredients && data.recipe.ingredients.length > 0) {
                data.recipe.ingredients.forEach(ingredient => {
                    const li = document.createElement('li');
                    li.textContent = ingredient;
                    ingredientsList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'No ingredients available';
                ingredientsList.appendChild(li);
            }

            // Populate instructions
            if (data.recipe.instructions && data.recipe.instructions.length > 0) {
                data.recipe.instructions.forEach(instruction => {
                    const li = document.createElement('li');
                    li.textContent = instruction;
                    instructionsList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'No instructions available';
                instructionsList.appendChild(li);
            }
            
        } catch (error) {
            console.error('Error:', error);
            foodName.textContent = 'Error: ' + error.message;
            ingredientsList.innerHTML = '';
            instructionsList.innerHTML = '';
        }
    }
});