function showAppTab(tab, event) {
    const contents = document.querySelectorAll('.app-content');
    const tabs = document.querySelectorAll('.app-tab');

    contents.forEach(content => content.style.display = 'none');
    tabs.forEach(t => t.classList.remove('active'));

    document.getElementById(tab).style.display = 'block';
    event.target.classList.add('active');
}

async function compressFile(type) {
    const input = document.getElementById(`${type}-upload`);
    const result = document.getElementById(`${type}-result`);
    const progress = document.getElementById(`${type}-progress`);

    result.textContent = '';  // Clear previous message
    progress.style.display = 'block'; // Show progress bar

    if (!input.files[0]) {
        result.textContent = 'Please upload a file.';
        progress.style.display = 'none';
        return;
    }

    const formData = new FormData();
    formData.append('file', input.files[0]);

    try {
        const response = await fetch(`/compress/${type}`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });

        const data = await response.json();
        progress.style.display = 'none'; // Hide progress bar

        if (data.success) {
            result.innerHTML = `
                <strong>Compression Successful!</strong><br>
                Original Size: ${data.original_size} bytes<br>
                Compressed Size: ${data.compressed_size} bytes<br>
                Compression Ratio: ${data.ratio.toFixed(2)}%<br>
                <a href="${data.compressed_file}" download class="cta-button">Download Compressed File</a>
                
            `;
        } else {
            result.textContent = `Failed: ${data.message}`;
        }
    } catch (error) {
        result.textContent = 'Error during compression. Please try again.';
        progress.style.display = 'none'; // Hide progress on error
        console.error(error);
    }
}
