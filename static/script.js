// Function to handle the recommendation request
async function updateSelectedSong() {
    const dropdown = document.getElementById('songDropdown');
    const selectedSongPlayer = document.getElementById('selectedSongPlayer');
    const selectedSongIndex = dropdown.selectedIndex;

    if (selectedSongIndex > 0) {
        // Get the selected song's ID from the dropdown
        const selectedOption = dropdown.options[selectedSongIndex];
        const trackID = selectedOption.getAttribute('data-track-id');

        // Update the embedded player with the selected song
        selectedSongPlayer.src = `https://open.spotify.com/embed/track/${trackID}`;
        
        // Fetch and display recommendations
        await getRecommendations(selectedSongIndex - 1);
    }
}

async function getRecommendations(songIndex) {
    // Send POST request to get recommendations
    const response = await fetch('/recommend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ song_index: songIndex }),
    });

    const recommendations = await response.json();

    console.log(recommendations);

    // Display recommendations
    const recommendationsDiv = document.getElementById('recommendations');
    recommendationsDiv.innerHTML = ''; // Clear previous recommendations

    recommendations.forEach(song => {
        const songDiv = document.createElement('div');
        songDiv.style.marginBottom = '20px';

        songDiv.innerHTML = `
            <h2>${song['Track Name']} - ${song['Artists']}</h2>
            <iframe src= "https://open.spotify.com/embed/track/${song['Track ID']}" 
            width="300" 
            height="80" 
            frameborder="0" 
            allowtransparency="true" 
            allow="encrypted-media"></iframe>
        `;
        console.log(song['Track URL']);
        recommendationsDiv.appendChild(songDiv);
    });
}
