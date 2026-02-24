class LionsFluteApp {
    constructor() {
        this.selectedFile = null;
        this.currentTask = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {

        // File select
        const fileInput = document.getElementById('audioFile');
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.selectedFile = e.target.files[0];
                this.showMessage(`Selected: ${this.selectedFile.name}`, "success");
            }
        });

        // Split button
        document.getElementById('splitBtn')
            .addEventListener('click', () => this.processAudio('split'));

        // Effect button
        document.getElementById('effectBtn')
            .addEventListener('click', () => this.processAudio('effect'));
    }

    async processAudio(type) {

        if (!this.selectedFile) {
            this.showMessage("Please select a file first", "error");
            return;
        }

        this.showLoading(true);
        this.showMessage("Uploading file...", "info");

        try {
            const formData = new FormData();
            formData.append('file', this.selectedFile);

            const endpoint = type === "split" ? "/split" : "/apply-effect";

            const response = await fetch(endpoint, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error("Upload failed");
            }

            const data = await response.json();

            if (!data.task_id) {
                throw new Error("Task ID not received");
            }

            this.currentTask = {
                id: data.task_id,
                type: type
            };

            this.showMessage("Processing started...", "info");
            this.pollTaskStatus();

        } catch (error) {
            this.showLoading(false);
            this.showMessage(error.message, "error");
        }
    }

    async pollTaskStatus() {

        if (!this.currentTask) return;

        try {
            const response = await fetch(`/task/${this.currentTask.id}`);
            const data = await response.json();

            if (data.status === "processing") {
                setTimeout(() => this.pollTaskStatus(), 2000);
            }

            else if (data.status === "completed") {
                this.showLoading(false);
                this.handleTaskCompletion(data);
            }

            else if (data.status === "failed") {
                this.showLoading(false);
                this.showMessage(data.error || "Processing failed", "error");
            }

        } catch (error) {
            this.showLoading(false);
            this.showMessage("Server connection error", "error");
        }
    }

    handleTaskCompletion(data) {

        this.showMessage("Processing completed successfully!", "success");

        if (!data.result) {
            this.showMessage("No result received", "error");
            return;
        }

        const resultDiv = document.getElementById("resultArea");
        resultDiv.innerHTML = "";

        if (data.result.vocal && data.result.instrumental) {

            resultDiv.appendChild(this.createDownloadButton(
                data.result.vocal,
                "Download Vocals"
            ));

            resultDiv.appendChild(this.createDownloadButton(
                data.result.instrumental,
                "Download Instrumental"
            ));
        }

        else if (data.result.output) {

            resultDiv.appendChild(this.createDownloadButton(
                data.result.output,
                "Download Processed File"
            ));
        }
    }

    createDownloadButton(filename, label) {

        const button = document.createElement("button");
        button.innerText = label;
        button.className = "download-btn";

        button.onclick = () => {
            window.location.href = `/download/${filename}`;
        };

        return button;
    }

    showLoading(show) {

        const loader = document.getElementById("loadingSpinner");
        if (!loader) return;

        loader.style.display = show ? "block" : "none";
    }

    showMessage(message, type) {

        const messageDiv = document.getElementById("messageArea");
        if (!messageDiv) return;

        messageDiv.innerText = message;
        messageDiv.className = type;

        setTimeout(() => {
            messageDiv.innerText = "";
        }, 5000);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new LionsFluteApp();
});