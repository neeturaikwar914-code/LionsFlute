// ================= CONFIG =================

const BASE_URL = window.location.origin;

// ================= MAIN FUNCTION =================

async function uploadAndProcess(type) {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file first");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    // If effect mode
    if (type === "effect") {
        const effect = document.getElementById("effectSelect").value;
        const intensity = document.getElementById("intensityRange").value;

        formData.append("effect", effect);
        formData.append("intensity", intensity);
    }

    const endpoint =
        type === "split"
            ? `${BASE_URL}/split`
            : `${BASE_URL}/apply_fx`;

    try {
        showMessage("Processing...", false);

        const response = await fetch(endpoint, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        const data = await response.json();

        if (!data.task_id) {
            throw new Error("Task ID missing");
        }

        pollTaskStatus(data.task_id);

    } catch (error) {
        console.error("FETCH ERROR:", error);
        showMessage("Failed to fetch - Server not reachable", true);
    }
}

// ================= POLLING =================

async function pollTaskStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${BASE_URL}/task/${taskId}`);
            const data = await response.json();

            if (data.status === "completed") {
                clearInterval(interval);
                showResult(data);
            }

            if (data.status === "failed") {
                clearInterval(interval);
                showMessage("Processing failed", true);
            }

        } catch (error) {
            clearInterval(interval);
            showMessage("Connection lost", true);
        }
    }, 2000);
}

// ================= RESULT DISPLAY =================

function showResult(data) {
    const resultBox = document.getElementById("resultBox");
    resultBox.innerHTML = "";

    if (data.type === "split") {
        const vocalUrl = `${BASE_URL}/download/${data.result.vocal}`;
        const instrumentalUrl = `${BASE_URL}/download/${data.result.instrumental}`;

        resultBox.innerHTML = `
            <h3>Download Files</h3>
            <a href="${vocalUrl}" target="_blank">Download Vocal</a><br><br>
            <a href="${instrumentalUrl}" target="_blank">Download Instrumental</a>
        `;
    }

    if (data.type === "effect") {
        const outputUrl = `${BASE_URL}/download/${data.result.output}`;

        resultBox.innerHTML = `
            <h3>Download File</h3>
            <a href="${outputUrl}" target="_blank">Download Processed Audio</a>
        `;
    }

    showMessage("Processing Complete ✅", false);
}

// ================= MESSAGE =================

function showMessage(text, isError) {
    const messageBox = document.getElementById("messageBox");
    messageBox.innerText = text;
    messageBox.style.color = isError ? "red" : "white";
}