# API

## Connect it to your Next.js skills

```ts
const res = await fetch("http://localhost:8000/ask/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question }),
});
const reader = res.body!.getReader();
const decoder = new TextDecoder();
let buffer = "";
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const events = buffer.split("\n\n");
  buffer = events.pop()!;                      // keep any incomplete event for the next chunk
  for (const e of events) {
    const data = JSON.parse(e.replace("data: ", ""));
    if (data.type === "step") setStatus(data.message);
    if (data.type === "answer") setAnswer(data.answer);
  }
}
```
