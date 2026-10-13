
document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("topic-images");
    const preview = document.getElementById("image-preview");

    // Không chạy nếu trang hiện tại không có form ảnh Forum.
    if (!input || !preview) return;

    input.addEventListener("change", function () {
        preview.replaceChildren();

        const files = Array.from(input.files);

        if (files.length > 4) {
            alert("Bạn chỉ được chọn tối đa 4 ảnh.");
            input.value = "";
            return;
        }

        files.forEach(function (file) {
            if (!file.type.startsWith("image/")) return;

            const img = document.createElement("img");
            img.alt = "Ảnh xem trước";
            img.className = "forum-image-preview-item";

            const objectUrl = URL.createObjectURL(file);
            img.src = objectUrl;

            img.onload = function () {
                URL.revokeObjectURL(objectUrl);
            };

            img.onerror = function () {
                URL.revokeObjectURL(objectUrl);
                img.remove();
            };

            preview.appendChild(img);
        });
    });
});
