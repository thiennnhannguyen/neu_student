/** Nội dung do nhóm biên soạn đánh dấu mã bằng dấu `. Hiện thành thẻ code, không chèn HTML thô. */
export default function InlineCode({ text }) {
  return text.split('`').map((part, index) =>
    index % 2 === 1 ? (
      // Vị trí trong chuỗi cố định, nội dung không đổi thứ tự.
      <code key={index}>{part}</code>
    ) : (
      part
    ),
  );
}
