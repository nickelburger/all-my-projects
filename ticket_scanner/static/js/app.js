document.addEventListener('DOMContentLoaded', () => {
    if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
        // Initialize QuaggaJS
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector('#interactive'),
                constraints: {
                    facingMode: "environment" // Use the back camera on mobile
                }
            },
            decoder: {
                readers: ["code_128_reader", "ean_reader", "ean_8_reader", "upc_reader"]
            }
        }, function(err) {
            if (err) {
                console.error("Quagga init error:", err); // More detailed error logging
                alert("Error initializing camera: " + err.message);
                return;
            }
            Quagga.start();
        });

        // On barcode detection
        Quagga.onDetected(result => {
            const code = result.codeResult.code;
            document.getElementById('result').textContent = "Scanned: " + code;

            // Send the scanned code to the backend to update the database
            fetch('/update_scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code: code })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').textContent = `Result: ${data.result}`;
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    } else {
        alert("Camera access not supported by your browser.");
    }
});

document.getElementById('search-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const searchTerm = document.getElementById('search-input').value;

    fetch(`/search?query=${searchTerm}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('search-result').textContent = 
                    `Found: ${data.record.first_name} ${data.record.last_name}, Scanned: ${data.record.scanned}`;
            } else {
                document.getElementById('search-result').textContent = "No record found.";
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
});
