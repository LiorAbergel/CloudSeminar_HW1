const FUNCTION_URL = "https://2fdl56o2kppjedibpmzbaetuay0hvzec.lambda-url.us-east-1.on.aws/"

let userId = localStorage.getItem("chat_user_id");
if (!userId) {
  userId = crypto.randomUUID();
  localStorage.setItem("chat_user_id", userId);
}

const chatEl = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("prompt");
const button = form.querySelector("button");

const totalTimes = [];
const openaiTimes = [];
const chart = new Chart(document.getElementById("timesChart"), {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "Total Request Time (ms)", data: totalTimes },
      { label: "OpenAI API Time (ms)", data: openaiTimes },
    ],
  },
  options: {
    scales: {
      x: { title: { display: true, text: "Request #" } },
      y: { beginAtZero: true, title: { display: true, text: "ms" } },
    },
  },
});

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

const average = (arr) =>
  arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : 0;

function updateStats(totalMs, openaiMs) {
  totalTimes.push(totalMs);
  openaiTimes.push(openaiMs);
  chart.data.labels.push(totalTimes.length);
  chart.update();
  document.getElementById("avgTotal").textContent = average(totalTimes);
  document.getElementById("avgOpenai").textContent = average(openaiTimes);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = input.value.trim();
  if (!prompt) return;

  addMessage("user", prompt);
  input.value = "";
  button.disabled = true;

  const start = performance.now();
  try {
    const res = await fetch(FUNCTION_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_prompt: prompt, user_id: userId }),
    });
    const data = await res.json();
    const totalMs = Math.round(performance.now() - start);

    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    addMessage("bot", data.ai_reply);
    updateStats(totalMs, data.openai_response_time_ms);
  } catch (err) {
    addMessage("error", `Error: ${err.message}`);
  } finally {
    button.disabled = false;
    input.focus();
  }
});