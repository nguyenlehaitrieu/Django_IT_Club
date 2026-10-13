
document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.getElementById("comment-content");
    const parentInput = document.getElementById("comment-parent-id");
    if (!textarea || !parentInput) return;
    document.querySelectorAll(".forum-reply-btn").forEach((button) => {
        button.addEventListener("click", () => {
            const commentId = button.dataset.commentId;
            const username = button.dataset.username;
            const mention = `@${username} `;
            parentInput.value = commentId;
            textarea.value = mention;
            textarea.placeholder = `Đang trả lời @${username}...`;
            textarea.focus();
            textarea.setSelectionRange(mention.length, mention.length);
            textarea.scrollIntoView({ behavior: "smooth", block: "center" });
        });
    });
});
    