async function fetchData() {
    try {
        const balance = await fetch('/api/balance').then(r => r.json());
        document.getElementById('balance').textContent = JSON.stringify(balance, null, 2);

        const orders = await fetch('/api/orders').then(r => r.json());
        document.getElementById('orders').textContent = JSON.stringify(orders, null, 2);

        const history = await fetch('/api/history').then(r => r.json());
        document.getElementById('history').textContent = JSON.stringify(history, null, 2);
    } catch (err) {
        console.error(err);
    }
}

fetchData();
setInterval(fetchData, 30000);
