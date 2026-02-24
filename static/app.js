class LionsFluteApp {
    constructor() {
        this.selectedFile = null;
        this.currentTask = null;

        this.init();
    }

    init() {
        this.initFileUpload();
        this.initButtons();
        this.initIntensitySlider();
    }

    // ---------------- FILE UPLOAD ----------------

    initFileUpload() {
        const fileInput = document.getElementById("audio-file");
        const uploadZone = document.getElementById("upload-zone");
        const processingSection = document.getElementById("processing-section");
        const audioPlayerSection = document.getElementById("audio-player-section");
        const audioElement = document.getElementById("audio-element");
        const fileNameDisplay = document.getElementById("current-file-name");

        uploadZone.addEventListener("click", () => fileInput.click());

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                this.selectedFile = e.target.files[0];

                fileNameDisplay.innerText = this.selectedFile.name;

                const objectURL = URL.createObjectURL(this.selectedFile);
                audioElement.src = objectURL;

                processingSection.style.display = "block";
                audioPlayerSection.style.display = "block";

                this.showStatus("File selected successfully", "info");
            }
        });
    }

    // ---------------- BUTTONS ----------------

    initButtons() {

        document.getElementById("split-btn")
            .addEventListener("click", () => this.processAudio("split"));

        document.getElementById("apply-fx-btn")
            .addEventListener("click", () => this.processAudio("effect"));

        document.getElementById("upload-form")
            .addEventListener("submit", (e) => e.preventDefault());
    }

    // ---------------- INTENSITY ----------------

    initIntensitySlider() {
        const slider = document.getElementById("intensity-range");
        const valueDisplay = document.getElementById("intensity-value");

        slider.addEventListener("input", () => {
            valueDisplay.innerText = slider.value;
        });
    }

    // ---------------- PROCESS AUDIO ----------------

    async processAudio(type) {

        if (!this.selectedFile) {
            this.showStatus("Please select a file first", "danger");
            return;
        }

        this.showProgress(true);

        try {
            const formData = new FormData();
            formData.append("file", this.selectedFile);

            if (type === "effect") {
                const effect = document.getElementById("effect-select").value;
                const intensity = document.getElementById("intensity-range").value;

                if (!effect) {
                    this.showStatus("Please select an effect", "danger");
                    this.showProgress(false);
                    return;
                }

                formData.append("effect", effect);
                formData.append("intensity", intensity);
            }

            const endpoint = type === "split" ? "/split" : "/apply-effect";

            const response = await fetch(endpoint, {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!data.task_id) throw new Error("No task ID returned");

            this.currentTask = {
                id: data.task_id,
                type: type
            };

            this.pollTask();

        } catch (err) {
            this.showProgress(false);
            this.showStatus(err.message, "danger");
        }
    }

    // ---------------- POLLING ----------------

    async pollTask() {

        if (!this.currentTask) return;

        try {
            const response = await fetch(`/task/${this.currentTask.id}`);
            const data = await response.json();

            if (data.status === "processing") {
                setTimeout(() => this.pollTask(), 2000);
            }

            else if (data.status === "completed") {
                this.showProgress(false);
                this.showResults(data.result);
            }

            else if (data.status === "failed") {
                this.showProgress(false);
                this.showStatus(data.error || "Processing failed", "danger");
            }

        } catch (err) {
            this.showProgress(false);
            this.showStatus("Server error", "danger");
        }
    }

    // ---------------- RESULTS ----------------

    showResults(result) {

        const resultsSection = document.getElementById("results-section");
        const resultsList = document.getElementById("results-list");
        const filesCount = document.getElementById("files-count");

        resultsList.innerHTML = "";

        let count = 0;

        if (result.vocal && result.instrumental) {
            resultsList.appendChild(this.createDownloadCard(result.vocal, "Vocals"));
            resultsList.appendChild(this.createDownloadCard(result.instrumental, "Instrumental"));
            count = 2;
        }

        if (result.output) {
            resultsList.appendChild(this.createDownloadCard(result.output, "Processed File"));
            count = 1;
        }

        filesCount.innerText = `${count} file(s)`;
        resultsSection.style.display = "block";

        this.showStatus("Processing completed successfully", "success");
    }

    createDownloadCard(filename, label) {

        const div = document.createElement("div");
        div.className = "result-item";

        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center p-3 border rounded">
                <div>
                    <strong>${label}</strong><br>
                    <small>${filename}</small>
                </div>
                <a href="/download/${filename}" class="btn btn-success btn-sm">
                    <i class="fas fa-download"></i> Download
                </a>
            </div>
        `;

        return div;
    }

    // ---------------- UI HELPERS ----------------

    showStatus(message, type) {
        const alert = document.getElementById("status-alert");
        const msg = document.getElementById("status-message");

        alert.className = `alert alert-${type}`;
        msg.innerText = message;

        alert.classList.remove("d-none");
    }

    showProgress(show) {
        const container = document.getElementById("progress-bar-container");
        const progressBar = document.getElementById("progress-bar");

        if (show) {
            container.style.display = "block";
            progressBar.style.width = "100%";
        } else {
            container.style.display = "none";
            progressBar.style.width = "0%";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new LionsFluteApp();
});