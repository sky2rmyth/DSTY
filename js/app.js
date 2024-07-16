const apiKey = 'KYi69n9KzaRZQdHN';
const apiSecret = 'mJg8tZjniFOqQdgBcyIlVR5v2XuTbcGx';
const baseUrl = 'https://api.livescore-api.com/v1/';

async function fetchApi(endpoint) {
    const response = await fetch(`${baseUrl}${endpoint}`, {
        headers: {
            'x-api-key': apiKey,
            'x-api-secret': apiSecret
        }
    });
    return response.json();
}

async function getLiveScores() {
    const data = await fetchApi('scores/live.json');
    displayData(data.data.match, '实时比分');
}

async function getFixtures() {
    const data = await fetchApi('fixtures.json');
    displayData(data.data.match, '赛程');
}

async function getHistory() {
    const data = await fetchApi('scores/history.json');
    displayData(data.data.match, '历史数据');
}

async function getStandings() {
    const data = await fetchApi('standings.json');
    displayData(data.data.league, '积分榜');
}

async function getTopScorers() {
    const data = await fetchApi('top-scorers.json');
    displayData(data.data.scorer, '最佳射手');
}

function displayData(data, title) {
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = `<h2>${title}</h2>`;

    data.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.innerHTML = JSON.stringify(item); // 这里可以格式化显示数据
        contentDiv.appendChild(itemElement);
    });
}

document.getElementById('live-scores-link').addEventListener('click', getLiveScores);
document.getElementById('fixtures-link').addEventListener('click', getFixtures);
document.getElementById('history-link').addEventListener('click', getHistory);
document.getElementById('standings-link').addEventListener('click', getStandings);
document.getElementById('top-scorers-link').addEventListener('click', getTopScorers);
