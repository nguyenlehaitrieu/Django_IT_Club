
document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.getElementById("comment-content");

    if (!textarea) return;

    const panels = document.querySelectorAll(".forum-reaction-panel");
    const toggles = document.querySelectorAll(".forum-reaction-toggle");

    function insertText(value) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const current = textarea.value;

        const next =
            current.slice(0, start) +
            value +
            current.slice(end);

        if (next.length > Number(textarea.maxLength)) {
            textarea.focus();
            return;
        }

        textarea.value = next;
        textarea.focus();

        const cursor = start + value.length;
        textarea.setSelectionRange(cursor, cursor);
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function closePanels() {
        panels.forEach(panel => {
            panel.hidden = true;
        });

        toggles.forEach(button => {
            button.setAttribute("aria-expanded", "false");
        });
    }

    toggles.forEach(button => {
        button.addEventListener("click", () => {
            const panel = document.getElementById(button.dataset.panel);
            if (!panel) return;

            const shouldOpen = panel.hidden;
            closePanels();

            panel.hidden = !shouldOpen;
            button.setAttribute("aria-expanded", String(shouldOpen));
        });
    });

    document.querySelectorAll("[data-emoji]").forEach(button => {
        button.addEventListener("click", () => {
            insertText(button.dataset.emoji);
        });
    });

    document.querySelectorAll("[data-sticker]").forEach(button => {
        button.addEventListener("click", () => {
            const code = button.dataset.sticker;

            // Chỉ chấp nhận mã sticker đã định nghĩa.
            const allowed = [
                "thanks",
                "coding",
                "celebrate",
                "thinking",
                "love"
            ];

            if (!allowed.includes(code)) return;

            insertText(`[sticker:${code}] `);
        });
    });

    document.addEventListener("click", event => {
        if (
            !event.target.closest(".forum-reaction-panel") &&
            !event.target.closest(".forum-reaction-toggle")
        ) {
            closePanels();
        }
    });
});
