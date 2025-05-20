let nextPageToken = null;
const excludedKeywords = [
  "online",
  "video",
  "music",
  "lyrics",
  "song",
  "gaming",
  "video gaming",
  "entertainment",
  "funny",
  "trailer",
  "food",
  "recipe",
  "adult",
];

const educationalKeywords = [
  "education",
  "tutorial",
  "study",
  "lesson",
  "course",
  "learn",
  "school",
  "academy",
  "university",
  "knowledge",
  "skills",
  "lecture",
  "training",
  "science",
  "math",
  "engineering",
];

async function fetchVideos(query, loadMore = false) {
  const resultDiv = document.getElementById("result");
  const loadMoreButton = document.getElementById("loadMore");

  if (!loadMore) {
    resultDiv.innerHTML = "Searching...";
    nextPageToken = null;
  }

  try {
    const response = await fetch("http://127.0.0.1:5000/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, pageToken: nextPageToken }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Error: ${response.statusText}`);
    }

    const result = await response.json();
    if (result.error) {
      throw new Error(result.error);
    }

    // Filter videos for educational content
    const filteredResults = result.results.filter((video) => {
      const title = video.title.toLowerCase();
      const description = video.description?.toLowerCase() || "";

      // Exclude videos with unwanted keywords
      if (
        excludedKeywords.some(
          (word) => title.includes(word) || description.includes(word)
        )
      ) {
        return false;
      }

      // Include only videos with educational keywords
      return educationalKeywords.some(
        (word) => title.includes(word) || description.includes(word)
      );
    });

    // Display filtered results
    if (!loadMore) resultDiv.innerHTML = "";

    filteredResults.forEach((video) => {
      resultDiv.innerHTML += `
        <div class="video-card">
          <iframe 
              src="https://www.youtube.com/embed/${video.videoId}" 
              frameborder="0" 
              allowfullscreen>
          </iframe>
          <div class="video-details">
              <p class="video-title">${video.title}</p>
              <div class="channel-info">
                  <img 
                      src="${video.channelLogo}" 
                      alt="${video.channelName}" 
                      class="channel-logo"
                  >
                  <p class="channel-name">${video.channelName}</p>
              </div>
          </div>
        </div>
      `;
    });

    nextPageToken = result.nextPageToken;
    loadMoreButton.style.display = nextPageToken ? "block" : "none";

    if (filteredResults.length === 0) {
      alert("No educational content found for the search term.");
    }
  } catch (error) {
    console.error("An error occurred:", error.message);
    resultDiv.innerHTML = `<p class="error-message">${error.message}</p>`;
    loadMoreButton.style.display = "none";
  }
}

document.getElementById("loadMore").addEventListener("click", () => {
  const query = document.getElementById("query").value;
  fetchVideos(query, true); // Pass `true` to indicate it's a load-more action
});

document
  .getElementById("summarizeForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const videoLink = document.getElementById("videoLink").value;
    const chatbotLoader = document.getElementById("chatbotLoader");
    const chatbotResponse = document.getElementById("chatbotResponse");
    const languageDropdown = document.getElementById("languageDropdown");

    chatbotLoader.style.display = "block";
    chatbotResponse.innerHTML = "";

    try {
      const response = await fetch("http://127.0.0.1:5000/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ videoLink }),
      });

      if (!response.ok) throw new Error(`Error: ${response.statusText}`);
      const result = await response.json();

      chatbotLoader.style.display = "none";
      chatbotResponse.innerHTML = `<p><strong>Summary:</strong> ${result.summary}</p>`;

      // Enable language dropdown
      languageDropdown.style.display = "block";
      languageDropdown.dataset.summary = result.summary;
    } catch (error) {
      chatbotLoader.style.display = "none";
      chatbotResponse.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
    }
  });

document.getElementById("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = document.getElementById("query").value;
  fetchVideos(query);
});

document
  .getElementById("summarizeForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const videoLink = document.getElementById("videoLink").value;
    const chatbotLoader = document.getElementById("chatbotLoader");
    const chatbotResponse = document.getElementById("chatbotResponse");

    chatbotLoader.style.display = "block";
    chatbotResponse.innerHTML = "";

    try {
      const response = await fetch("http://127.0.0.1:5000/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ videoLink }),
      });

      if (!response.ok) throw new Error(`Error: ${response.statusText}`);

      const result = await response.json();
      chatbotLoader.style.display = "none";

      // Extract video ID from the provided link for thumbnail and title
      const videoId =
        new URL(videoLink).searchParams.get("v") || videoLink.split("/").pop();

      chatbotResponse.innerHTML = `
        <div class="summary-card">
          <img 
            src="https://img.youtube.com/vi/${videoId}/hqdefault.jpg" 
            alt="Video Thumbnail" 
            class="summary-thumbnail"
          />
          <div class="summary-details">
            <p><strong>Summary:</strong> ${result.summary}</p>
          </div>
        </div>
      `;
    } catch (error) {
      chatbotLoader.style.display = "none";
      chatbotResponse.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
    }
  });

document
  .getElementById("languageDropdown")
  .addEventListener("change", async (e) => {
    const targetLanguage = e.target.value;
    const summary = e.target.dataset.summary;
    const chatbotResponse = document.getElementById("chatbotResponse");

    if (targetLanguage) {
      try {
        const response = await fetch("http://127.0.0.1:5000/translate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ summary, language: targetLanguage }),
        });

        if (!response.ok) throw new Error("Translation failed.");

        const result = await response.json();
        chatbotResponse.innerHTML += `<p><strong>Translated Summary:</strong> ${result.translatedSummary}</p>`;
      } catch (error) {
        chatbotResponse.innerHTML += `<p class="error-message">Error: ${error.message}</p>`;
      }
    }
  });
