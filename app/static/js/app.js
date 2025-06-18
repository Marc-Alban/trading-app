// Configuration
const API_BASE_URL = window.location.origin;
const API_PREFIX = '/api';
const DEFAULT_PAIR = 'BTCUSD';
const REFRESH_INTERVAL = 10000; // 10 secondes
let tradingChart = null;
let priceData = [];
let timeData = [];

// Fonctions utilitaires
async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
        showAlert('danger', `Erreur: ${error.message}`);
        return null;
    }
}

async function postData(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        return await response.json();
    } catch (error) {
        console.error('Erreur lors de l\'envoi des données:', error);
        showAlert('danger', `Erreur: ${error.message}`);
        return null;
    }
}

function showAlert(type, message) {
    const alertsContainer = document.getElementById('alerts-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 500);
    }, 5000);
}

function formatCurrency(value, decimals = 2) {
    return parseFloat(value).toFixed(decimals);
}

// Mise à jour du solde
async function updateBalance() {
    const data = await fetchData('/balance');
    if (data && data.status === 'success') {
        const balanceContainer = document.getElementById('balance-container');
        let html = '<div class="list-group">';
        
        let totalInUSD = 0;
        
        for (const [currency, amount] of Object.entries(data.data)) {
            // Ignorer les montants nuls ou très petits
            if (parseFloat(amount) < 0.00001) continue;
            
            // Format currency name
            let currencyName = currency;
            if (currency.startsWith('X') || currency.startsWith('Z')) {
                currencyName = currency.slice(1);
            }
            
            let badgeClass = 'bg-primary';
            if (currencyName === 'BTC' || currencyName === 'ETH') {
                badgeClass = 'bg-success';
            } else if (currencyName === 'USD' || currencyName === 'EUR') {
                badgeClass = 'bg-info';
            }
            
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>${currencyName}</span>
                    <span class="badge ${badgeClass} rounded-pill">${formatCurrency(amount, 8)}</span>
                </div>
            `;
        }
        
        html += '</div>';
        balanceContainer.innerHTML = html;
    }
}

// Mise à jour de l'analyse du marché
async function updateMarketAnalysis() {
    const pair = document.getElementById('pair-selector').value || DEFAULT_PAIR;
    const data = await fetchData(`/analyze/${pair}`);
    if (data && data.status === 'success') {
        const analysisContainer = document.getElementById('market-analysis-container');
        const analysis = data.data;
        
        displayMarketAnalysis(analysis);
    }
}

function displayMarketAnalysis(analysis) {
    const analysisContainer = document.getElementById('market-analysis-container');
    
    // Déterminer les classes pour la recommandation
    let recommendationClass = 'text-secondary';
    let confidenceClass = 'bg-secondary';
    
    if (analysis.recommendation === 'buy') {
        recommendationClass = 'text-success';
        confidenceClass = 'bg-success';
    } else if (analysis.recommendation === 'sell') {
        recommendationClass = 'text-danger';
        confidenceClass = 'bg-danger';
    }
    
    // Calculer le pourcentage de confiance
    const confidencePercent = (analysis.confidence * 100).toFixed(1);
    
    const html = `
        <div class="row mb-3">
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">Tendance</h6>
                        <p class="card-text fs-4 ${recommendationClass}">${analysis.trend.toUpperCase()}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">Recommandation</h6>
                        <p class="card-text fs-4 ${recommendationClass} fw-bold">${analysis.recommendation.toUpperCase()}</p>
                        <div class="progress mt-2">
                            <div class="progress-bar ${confidenceClass}" role="progressbar" style="width: ${confidencePercent}%;" 
                                 aria-valuenow="${confidencePercent}" aria-valuemin="0" aria-valuemax="100">
                                ${confidencePercent}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-4">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">RSI</h6>
                        <p class="card-text">${analysis.indicators.rsi.toFixed(2)}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">MACD</h6>
                        <p class="card-text">
                            Signal: ${analysis.indicators.macd.signal.toFixed(2)}<br>
                            MACD: ${analysis.indicators.macd.macd.toFixed(2)}<br>
                            Hist: ${analysis.indicators.macd.histogram.toFixed(2)}
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">Bandes de Bollinger</h6>
                        <p class="card-text">
                            Haut: ${analysis.indicators.bollinger_bands.upper.toFixed(2)}<br>
                            Milieu: ${analysis.indicators.bollinger_bands.middle.toFixed(2)}<br>
                            Bas: ${analysis.indicators.bollinger_bands.lower.toFixed(2)}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">Support</h6>
                        <p class="card-text">${analysis.support_levels[0].toFixed(2)}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">Résistance</h6>
                        <p class="card-text">${analysis.resistance_levels[0].toFixed(2)}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    analysisContainer.innerHTML = html;
}

// Mise à jour des ordres ouverts
async function updateOpenOrders() {
    const data = await fetchData('/orders/open');
    if (data && data.status === 'success') {
        const ordersContainer = document.getElementById('open-orders-container');
        
        // Si aucun ordre ouvert
        if (!data.data.open || Object.keys(data.data.open).length === 0) {
            ordersContainer.innerHTML = '<div class="alert alert-info">Aucun ordre ouvert</div>';
            return;
        }
        
        let html = '<div class="list-group">';
        
        for (const [orderId, order] of Object.entries(data.data.open)) {
            const typeClass = order.descr.type === 'buy' ? 'text-success' : 'text-danger';
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${order.descr.pair}</h6>
                        <small class="${typeClass} fw-bold">${order.descr.type.toUpperCase()}</small>
                    </div>
                    <p class="mb-1">Volume: ${order.vol}</p>
                    <small>Prix: ${order.descr.price || 'Market'}</small>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-danger cancel-order-btn" data-order-id="${orderId}">
                            Annuler
                        </button>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        ordersContainer.innerHTML = html;
        
        // Ajouter les écouteurs d'événement pour les boutons d'annulation
        document.querySelectorAll('.cancel-order-btn').forEach(button => {
            button.addEventListener('click', function() {
                cancelOrder(this.dataset.orderId);
            });
        });
    }
}

// Mise à jour de l'historique des trades
async function updateTradeHistory() {
    const data = await fetchData('/history');
    if (data && data.status === 'success') {
        const historyContainer = document.getElementById('history-container');
        
        // Si aucun historique
        if (!data.data || data.data.length === 0) {
            historyContainer.innerHTML = '<div class="alert alert-info">Aucun historique de trade disponible</div>';
            return;
        }
        
        let html = '<div class="table-responsive"><table class="table table-striped table-sm">';
        html += `
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Paire</th>
                    <th>Type</th>
                    <th>Prix</th>
                    <th>Volume</th>
                    <th>Coût</th>
                    <th>Frais</th>
                    <th>Statut</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        for (const trade of data.data) {
            const typeClass = trade.type === 'buy' ? 'text-success' : 'text-danger';
            const date = new Date(trade.time).toLocaleString();
            
            html += `
                <tr>
                    <td>${date}</td>
                    <td>${trade.pair}</td>
                    <td class="${typeClass}">${trade.type.toUpperCase()}</td>
                    <td>${formatCurrency(trade.price)}</td>
                    <td>${formatCurrency(trade.volume, 8)}</td>
                    <td>${formatCurrency(trade.cost)}</td>
                    <td>${formatCurrency(trade.fee)}</td>
                    <td>${trade.status}</td>
                </tr>
            `;
        }
        
        html += '</tbody></table></div>';
        historyContainer.innerHTML = html;
    }
}

// Initialisation du graphique
function initTradingChart() {
    const ctx = document.getElementById('trading-chart').getContext('2d');
    tradingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeData,
            datasets: [{
                label: 'Prix',
                data: priceData,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                borderWidth: 2,
                tension: 0.2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 0,
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Prix: ${formatCurrency(context.raw)}`;
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
}

// Mise à jour du graphique
async function updateTradingChart() {
    const pair = document.getElementById('pair-selector').value || DEFAULT_PAIR;
    const data = await fetchData(`/ticker/${pair}`);
    if (data && data.status === 'success') {
        const price = parseFloat(data.data.c[0]);
        const timestamp = new Date().toLocaleTimeString();
        
        // Ajouter les données
        timeData.push(timestamp);
        priceData.push(price);
        
        // Limiter le nombre de points dans le graphique
        const maxPoints = 30;
        if (timeData.length > maxPoints) {
            timeData.shift();
            priceData.shift();
        }
        
        // Mettre à jour le graphique
        tradingChart.data.labels = timeData;
        tradingChart.data.datasets[0].data = priceData;
        tradingChart.update();
        
        // Mettre à jour le titre du graphique
        document.getElementById('chart-title').textContent = `${pair} - ${formatCurrency(price)}`;
    }
}

// Trading automatique
async function autoTrade(event) {
    const button = event.currentTarget;
    const pair = button.dataset.pair;
    
    // Désactiver le bouton pendant le traitement
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> En cours...';
    
    try {
        const result = await postData('/auto-trade', { pair });
        
        if (result.status === 'success') {
            const tradeResult = result.data;
            
            if (tradeResult.status === 'success') {
                showAlert('success', `Trade automatique effectué: ${tradeResult.type} ${formatCurrency(tradeResult.volume, 8)} ${pair} à ${formatCurrency(tradeResult.price)}`);
            } else if (tradeResult.status === 'no_trade') {
                showAlert('info', `Pas de trade: ${tradeResult.reason}`);
            }
        } else {
            showAlert('danger', `Erreur lors du trading automatique: ${result.detail || 'Erreur inconnue'}`);
        }
    } catch (error) {
        console.error('Erreur lors du trading automatique:', error);
        showAlert('danger', `Erreur: ${error.message}`);
    } finally {
        // Réactiver le bouton
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-lightning-charge"></i> Trading automatique';
        
        // Mettre à jour les données pertinentes
        updateBalance();
        updateOpenOrders();
    }
}

// Annuler un ordre
async function cancelOrder(orderId) {
    // Fonction à implémenter
    console.log(`Cancel order ${orderId}`);
    showAlert('warning', `Annulation d'ordre non implémentée: ${orderId}`);
}

// Changer de paire de trading
function changeTradingPair() {
    // Réinitialiser les données du graphique
    timeData = [];
    priceData = [];
    
    // Mettre à jour l'interface
    updateMarketAnalysis();
    updateTradingChart();
}

// Initialisation
function init() {
    // Initialiser le graphique
    initTradingChart();
    
    // Configuration de l'interface
    setupEventListeners();
    
    // Mettre à jour toutes les données
    updateBalance();
    updateMarketAnalysis();
    updateOpenOrders();
    updateTradeHistory();
    updateTradingChart();
    
    // Mise à jour périodique
    setInterval(() => {
        updateBalance();
        updateMarketAnalysis();
        updateOpenOrders();
        updateTradingChart();
    }, REFRESH_INTERVAL);
}

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Sélecteur de paire
    const pairSelector = document.getElementById('pair-selector');
    if (pairSelector) {
        pairSelector.addEventListener('change', changeTradingPair);
    }
    
    // Onglets
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const targetId = event.target.getAttribute('href');
            if (targetId === '#history-tab') {
                updateTradeHistory();
            }
        });
    });
}

// Démarrage de l'application
document.addEventListener('DOMContentLoaded', init);

document.addEventListener("DOMContentLoaded", function() {
    // Initialisation
    init();
    
    // Formulaire de placement d'ordre
    document.getElementById('order-form').addEventListener('submit', function(e) {
        e.preventDefault();
        placeOrder();
    });
    
    // Toggle pour le type d'ordre (limit/market)
    document.querySelectorAll('input[name="order-ordertype"]').forEach(input => {
        input.addEventListener('change', function() {
            togglePriceField();
        });
    });
    
    // Boutons de rafraîchissement
    document.querySelectorAll('.refresh-btn').forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            refreshData(target);
        });
    });
    
    // Trading automatique
    document.getElementById('auto-trade-btn-advanced').addEventListener('click', function() {
        const pair = this.getAttribute('data-pair');
        autoTrade(pair);
    });
    
    // Trading automatique en arrière-plan
    document.getElementById('auto-trade-background-btn').addEventListener('click', function() {
        const pair = this.getAttribute('data-pair');
        autoTradeBackground(pair);
    });
    
    // Formulaire des paramètres
    document.getElementById('settings-form').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });

    // Changement de paire de trading
    document.getElementById('pair-selector').addEventListener('change', function() {
        const pair = this.value;
        updateChartTitle(pair);
        refreshData('chart', pair);
        refreshData('market', pair);
    });
});

// Initialisation
function init() {
    // Charger les données initiales
    refreshData('balance');
    refreshData('market');
    refreshData('chart');
    refreshData('orders');
    
    // Charger les paramètres
    loadSettings();
    
    // Configurer les champs du formulaire
    togglePriceField();
}

// Mise à jour du titre du graphique
function updateChartTitle(pair) {
    document.getElementById('chart-title').textContent = `Graphique ${pair}`;
    
    // Mettre à jour le bouton de trading automatique
    document.getElementById('auto-trade-btn-advanced').setAttribute('data-pair', pair);
    document.getElementById('auto-trade-background-btn').setAttribute('data-pair', pair);
}

// Toggle pour afficher/masquer le champ de prix
function togglePriceField() {
    const orderType = document.querySelector('input[name="order-ordertype"]:checked').value;
    const priceField = document.querySelector('.order-price-field');
    
    if (orderType === 'limit') {
        priceField.classList.remove('d-none');
    } else {
        priceField.classList.add('d-none');
    }
}

// Rafraîchir les données
async function refreshData(target, pair = null) {
    if (!pair && (target === 'chart' || target === 'market')) {
        pair = document.getElementById('pair-selector').value;
    }
    
    try {
        switch (target) {
            case 'balance':
                await fetchBalance();
                break;
            case 'market':
                await fetchMarketAnalysis(pair);
                break;
            case 'chart':
                await fetchChartData(pair);
                break;
            case 'orders':
                await fetchOrders();
                break;
            case 'history':
                await fetchHistory();
                break;
        }
    } catch (error) {
        showAlert('error', `Erreur lors du rafraîchissement des données: ${error.message}`);
    }
}

// Récupérer le solde
async function fetchBalance() {
    try {
        const response = await fetch('/api/balance');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayBalance(data.data);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de la récupération du solde:', error);
        showAlert('error', `Erreur lors de la récupération du solde: ${error.message}`);
    }
}

// Afficher le solde
function displayBalance(balance) {
    const container = document.getElementById('balance-container');
    let html = '<table class="table table-striped"><thead><tr><th>Devise</th><th>Montant</th></tr></thead><tbody>';
    
    for (const [currency, amount] of Object.entries(balance)) {
        // Filtrer pour n'afficher que les soldes non nuls
        if (amount > 0) {
            const formattedAmount = parseFloat(amount).toFixed(6);
            const currencyName = formatCurrencyName(currency);
            html += `<tr><td>${currencyName}</td><td>${formattedAmount}</td></tr>`;
        }
    }
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Formater les noms de devises
function formatCurrencyName(currency) {
    const mapping = {
        'ZUSD': 'USD',
        'XXBT': 'BTC',
        'XETH': 'ETH',
    };
    
    return mapping[currency] || currency;
}

// Récupérer l'analyse du marché
async function fetchMarketAnalysis(pair) {
    try {
        const response = await fetch(`/api/market/analysis/${pair}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayMarketAnalysis(data.data);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de l\'analyse du marché:', error);
        showAlert('error', `Erreur lors de la récupération de l'analyse: ${error.message}`);
    }
}

// Récupérer les données pour le graphique
async function fetchChartData(pair) {
    try {
        const response = await fetch(`/api/ohlc/${pair}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayChart(data.data, pair);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de la récupération des données du graphique:', error);
        showAlert('error', `Erreur lors de la récupération des données du graphique: ${error.message}`);
    }
}

// Afficher le graphique
function displayChart(ohlcData, pair) {
    const ctx = document.getElementById('trading-chart').getContext('2d');
    
    // Détruire le graphique existant s'il y en a un
    if (window.tradingChart) {
        window.tradingChart.destroy();
    }
    
    // Préparer les données
    const labels = [];
    const prices = [];
    
    ohlcData.forEach(candle => {
        const date = new Date(candle[0] * 1000);
        labels.push(formatDate(date));
        prices.push(parseFloat(candle[4])); // Prix de clôture
    });
    
    // Créer le graphique
    window.tradingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `Prix ${pair}`,
                data: prices,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                pointRadius: 0,
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

// Formater une date
function formatDate(date) {
    return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
}

// Récupérer les ordres
async function fetchOrders() {
    try {
        const response = await fetch('/api/orders');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayOrders(data.data);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de la récupération des ordres:', error);
        showAlert('error', `Erreur lors de la récupération des ordres: ${error.message}`);
    }
}

// Afficher les ordres
function displayOrders(orders) {
    const container = document.getElementById('orders-container');
    const openOrdersContainer = document.getElementById('open-orders-container');
    
    if (Object.keys(orders).length === 0) {
        const html = '<div class="alert alert-info">Aucun ordre ouvert</div>';
        container.innerHTML = html;
        if (openOrdersContainer) {
            openOrdersContainer.innerHTML = html;
        }
        return;
    }
    
    let html = `
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Paire</th>
                    <th>Type</th>
                    <th>Prix</th>
                    <th>Volume</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    for (const [id, order] of Object.entries(orders)) {
        const shortId = id.substring(0, 8) + '...';
        html += `
            <tr>
                <td>${shortId}</td>
                <td>${order.descr.pair}</td>
                <td class="${order.descr.type === 'buy' ? 'text-success' : 'text-danger'}">${order.descr.type.toUpperCase()}</td>
                <td>${order.descr.price || 'Market'}</td>
                <td>${order.vol}</td>
                <td>
                    <button class="btn btn-sm btn-danger cancel-order" data-id="${id}">
                        <i class="bi bi-x-circle"></i> Annuler
                    </button>
                </td>
            </tr>
        `;
    }
    
    html += '</tbody></table>';
    
    container.innerHTML = html;
    if (openOrdersContainer) {
        openOrdersContainer.innerHTML = html;
    }
    
    // Ajouter les écouteurs pour les boutons d'annulation
    document.querySelectorAll('.cancel-order').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-id');
            cancelOrder(orderId);
        });
    });
}

// Annuler un ordre
async function cancelOrder(orderId) {
    try {
        const response = await fetch(`/api/order/${orderId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showAlert('success', 'Ordre annulé avec succès');
            await fetchOrders();
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de l\'annulation de l\'ordre:', error);
        showAlert('error', `Erreur lors de l'annulation de l'ordre: ${error.message}`);
    }
}

// Récupérer l'historique
async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayHistory(data.data);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de la récupération de l\'historique:', error);
        showAlert('error', `Erreur lors de la récupération de l'historique: ${error.message}`);
    }
}

// Afficher l'historique
function displayHistory(history) {
    const container = document.getElementById('history-container');
    
    if (Object.keys(history).length === 0) {
        container.innerHTML = '<div class="alert alert-info">Aucun historique de trade</div>';
        return;
    }
    
    let html = `
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Paire</th>
                    <th>Type</th>
                    <th>Prix</th>
                    <th>Volume</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Tri par date décroissante
    const trades = Object.entries(history).sort((a, b) => b[1].time - a[1].time);
    
    for (const [id, trade] of trades) {
        const shortId = id.substring(0, 8) + '...';
        const date = new Date(trade.time * 1000);
        
        html += `
            <tr>
                <td>${shortId}</td>
                <td>${trade.pair}</td>
                <td class="${trade.type === 'buy' ? 'text-success' : 'text-danger'}">${trade.type.toUpperCase()}</td>
                <td>${parseFloat(trade.price).toFixed(2)}</td>
                <td>${parseFloat(trade.vol).toFixed(6)}</td>
                <td>${formatDate(date)}</td>
            </tr>
        `;
    }
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Placer un ordre
async function placeOrder() {
    try {
        const pair = document.getElementById('order-pair').value;
        const type = document.querySelector('input[name="order-type"]:checked').value;
        const ordertype = document.querySelector('input[name="order-ordertype"]:checked').value;
        const volume = document.getElementById('order-volume').value;
        const price = ordertype === 'limit' ? document.getElementById('order-price').value : null;
        
        const order = {
            pair: pair,
            order_type: type,
            order_ordertype: ordertype,
            volume: parseFloat(volume)
        };
        
        if (price) {
            order.price = parseFloat(price);
        }
        
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(order)
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showAlert('success', 'Ordre placé avec succès');
            document.getElementById('order-form').reset();
            await fetchOrders();
            await fetchBalance();
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors du placement de l\'ordre:', error);
        showAlert('error', `Erreur lors du placement de l'ordre: ${error.message}`);
    }
}

// Trading automatique
async function autoTrade(pair) {
    try {
        const button = document.getElementById('auto-trade-btn-advanced');
        button.disabled = true;
        button.innerHTML = '<i class="bi bi-arrow-repeat"></i> Analyse en cours...';
        
        const response = await fetch('/api/trade/auto', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pair })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const result = data.data;
            
            if (result.action === 'buy' || result.action === 'sell') {
                showAlert('success', `Trade automatique effectué: ${result.action.toUpperCase()} ${result.volume} ${pair} à $${result.price.toFixed(2)}`);
                await fetchOrders();
                await fetchBalance();
            } else {
                showAlert('info', `Pas de trade automatique: ${result.reason}`);
            }
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors du trading automatique:', error);
        showAlert('error', `Erreur lors du trading automatique: ${error.message}`);
    } finally {
        const button = document.getElementById('auto-trade-btn-advanced');
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-lightning-charge"></i> Trading Automatique';
    }
}

// Trading automatique en arrière-plan
async function autoTradeBackground(pair) {
    try {
        const button = document.getElementById('auto-trade-background-btn');
        button.disabled = true;
        
        const response = await fetch('/api/trade/auto/background', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pair })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showAlert('success', data.message);
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur lors de la programmation du trading automatique:', error);
        showAlert('error', `Erreur lors de la programmation du trading automatique: ${error.message}`);
    } finally {
        const button = document.getElementById('auto-trade-background-btn');
        button.disabled = false;
    }
}

// Charger les paramètres
function loadSettings() {
    const maxTradeAmount = localStorage.getItem('maxTradeAmount') || 1000;
    const riskPercentage = localStorage.getItem('riskPercentage') || 2;
    const stopLossPercentage = localStorage.getItem('stopLossPercentage') || 5;
    const takeProfitPercentage = localStorage.getItem('takeProfitPercentage') || 10;
    
    document.getElementById('max-trade-amount').value = maxTradeAmount;
    document.getElementById('risk-percentage').value = riskPercentage;
    document.getElementById('stop-loss-percentage').value = stopLossPercentage;
    document.getElementById('take-profit-percentage').value = takeProfitPercentage;
}

// Enregistrer les paramètres
function saveSettings() {
    const maxTradeAmount = document.getElementById('max-trade-amount').value;
    const riskPercentage = document.getElementById('risk-percentage').value;
    const stopLossPercentage = document.getElementById('stop-loss-percentage').value;
    const takeProfitPercentage = document.getElementById('take-profit-percentage').value;
    
    localStorage.setItem('maxTradeAmount', maxTradeAmount);
    localStorage.setItem('riskPercentage', riskPercentage);
    localStorage.setItem('stopLossPercentage', stopLossPercentage);
    localStorage.setItem('takeProfitPercentage', takeProfitPercentage);
    
    showAlert('success', 'Paramètres enregistrés avec succès');
} 