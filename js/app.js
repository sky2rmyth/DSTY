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
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

async function getLiveScores() {
    const data = await fetchApi('scores/live.json');
    displayData(data.data.match, '实时比分');
}

async function getFixtures() {
    const data = await fetchApi('fixtures/list.json');
    displayData(data.data.match, '赛程');
}

async function getHistory() {
    const data = await fetchApi('scores/history.json');
    displayData(data.data.match, '历史数据');
}

async function getStandings() {
    const data = await fetchApi('competitions/list.json');
    displayData(data.data.league, '积分榜');
}

async function getTopScorers() {
    const data = await fetchApi('top-scorers/list.json');
    displayData(data.data.scorer, '最佳射手');
}

function displayData(data, title) {
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = `<h2>${title}</h2>`;

    if (!data || data.length === 0) {
        contentDiv.innerHTML += '<p>没有数据。</p>';
        return;
    }

    data.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.innerHTML = JSON.stringify(item); // 这里你可以格式化显示数据
        contentDiv.appendChild(itemElement);
    });
}

document.getElementById('live-scores-link').addEventListener('click', async () => {
    try {
        await getLiveScores();
    } catch (error) {
        console.error('Error:', error);
    }
});

document.getElementById('fixtures-link').addEventListener('click', async () => {
    try {
        await getFixtures();
    } catch (error) {
        console.error('Error:', error);
    }
});

document.getElementById('history-link').addEventListener('click', async () => {
    try {
        await getHistory();
    } catch (error) {
        console.error('Error:', error);
    }
});

document.getElementById('standings-link').addEventListener('click', async () => {
    try {
        await getStandings();
    } catch (error) {
        console.error('Error:', error);
    }
});

document.getElementById('top-scorers-link').addEventListener('click', async () => {
    try {
        await getTopScorers();
    } catch (error) {
        console.error('Error:', error);
    }
});

// 每隔15分钟自动更新数据
setInterval(async () => {
    try {
        await getLiveScores();
    } catch (error) {
        console.error('Error:', error);
    }
}, 15 * 60 * 1000); // 15分钟 = 15 * 60 * 1000 毫秒
