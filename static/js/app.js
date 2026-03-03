const generateBtn = document.getElementById('generateBtn');
const spinner = document.getElementById('spinner');
const textInput = document.getElementById('textInput');
const resultsContainer = document.getElementById('results');
const audioPlayer = document.getElementById('audioPlayer');
const errorBox = document.getElementById('error');

function renderSentenceCard(item, idx) {
  const card = document.createElement('article');
  card.className = 'sentence-card';

  const emotionPairs = Object.entries(item.emotions)
    .sort((a, b) => b[1] - a[1])
    .map(([label, score]) => `${label}: ${score.toFixed(3)}`)
    .join(' | ');

  card.innerHTML = `
    <strong>Sentence ${idx + 1}</strong>
    <div>${item.text}</div>
    <div class="meta">
      <span>Dominant: ${item.dominant_emotion}</span>
      <span>Rate: ${item.rate}</span>
      <span>Volume: ${item.volume.toFixed(3)}</span>
    </div>
    <div class="emotions">${emotionPairs}</div>
  `;

  return card;
}

function setLoading(isLoading) {
  generateBtn.disabled = isLoading;
  spinner.classList.toggle('active', isLoading);
}

async function generateAudio() {
  const text = textInput.value.trim();

  errorBox.textContent = '';
  resultsContainer.innerHTML = '';

  if (!text) {
    errorBox.textContent = 'Please enter text before generating audio.';
    return;
  }

  setLoading(true);

  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Request failed.');
    }

    data.sentences.forEach((item, idx) => {
      resultsContainer.appendChild(renderSentenceCard(item, idx));
    });

    audioPlayer.src = `${data.audio_url}?t=${Date.now()}`;
    audioPlayer.load();
  } catch (error) {
    errorBox.textContent = error.message || 'Something went wrong while generating audio.';
  } finally {
    setLoading(false);
  }
}

generateBtn.addEventListener('click', generateAudio);
