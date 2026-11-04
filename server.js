const express = require("express");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const app = express();


const uploadDir = path.join(__dirname, "uploads");

if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}


app.use("/uploads", express.static("uploads"));


let lastResult = {
    result: "No data yet",
    image: ""
};


app.get("/ui", (req, res) => {
    res.sendFile(path.join(__dirname, "ui.html"));
});


app.post("/upload", (req, res) => {

    const type = req.query.type || "general";

    const folder = path.join(uploadDir, type);
    if (!fs.existsSync(folder)) fs.mkdirSync(folder);

    const fileName = `image_${Date.now()}.jpg`;
    const filePath = path.join(folder, fileName);

    const writeStream = fs.createWriteStream(filePath);
    req.pipe(writeStream);

    writeStream.on("finish", () => {

        console.log("📸 Image received:", fileName);

        exec(`py -3.11 analyze.py "${filePath}"`, (error, stdout) => {

            if (error) {
                console.log("❌ Python error");
                return res.status(500).send("error");
            }

            let result = stdout.trim();

            let formatted =
                result.includes("Correct") ? "✅ Correct Posture" :
                result.includes("Bad") ? "❌ Bad Posture" :
                "⚠️ Posture unclear";

            console.log("🧠 RESULT:", formatted);

            lastResult = {
                result: formatted,
                image: `/uploads/${type}/${fileName.replace(".jpg", "_output.jpg")}`
            };

            res.json(lastResult);
        });
    });

    writeStream.on("error", (err) => {
        console.log("❌ Save error:", err);
        res.status(500).send("error saving image");
    });
});


app.get("/last-result", (req, res) => {
    res.json(lastResult);
});


app.listen(8000, "0.0.0.0", () => {
    console.log("🚀 Server running:");
    console.log("👉 http://192.168.3.114:8000/ui");
});