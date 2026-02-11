/**
 * Chart Renderer for ConveAI Analytics
 * Automatically renders charts based on query results
 */

class ChartRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.charts = {};
    }

    /**
     * Detect appropriate chart type based on data shape
     */
    detectChartType(data) {
        if (!data || !data.length) return null;

        const keys = Object.keys(data[0]);
        const numericFields = keys.filter(k => typeof data[0][k] === 'number');
        const stringFields = keys.filter(k => typeof data[0][k] === 'string');

        // Time series: has date field + numeric values
        if (keys.some(k => k.toLowerCase().includes('date') || k.toLowerCase().includes('month') || k.toLowerCase().includes('year'))) {
            return 'line';
        }

        // Category comparison: 1 string dimension + numeric measures
        if (stringFields.length === 1 && numericFields.length >= 1 && data.length <= 20) {
            return 'bar';
        }

        // Distribution/parts-of-whole
        if (stringFields.length === 1 && numericFields.length === 1 && data.length <= 10) {
            return 'pie';
        }

        // Default to table for complex data
        return 'table';
    }

    /**
     * Render chart based on data
     */
    renderChart(data, chartType = null, options = {}) {
        if (!data || !data.length) {
            return this.renderEmpty();
        }

        const type = chartType || this.detectChartType(data);
        const chartId = `chart-${Date.now()}`;

        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        chartContainer.style.cssText = 'background: white; padding: 20px; border-radius: 8px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);';

        if (type === 'table') {
            this.renderTable(data, chartContainer);
        } else {
            const canvas = document.createElement('canvas');
            canvas.id = chartId;
            canvas.style.maxHeight = '400px';
            chartContainer.appendChild(canvas);

            this.renderCanvasChart(canvas, data, type, options);
        }

        return chartContainer;
    }

    /**
     * Render Chart.js chart on canvas
     */
    renderCanvasChart(canvas, data, type, options) {
        const keys = Object.keys(data[0]);
        const labelKey = keys.find(k => typeof data[0][k] === 'string') || keys[0];
        const valueKeys = keys.filter(k => typeof data[0][k] === 'number');

        const labels = data.map(row => row[labelKey]);
        const datasets = valueKeys.map((key, index) => ({
            label: this.formatLabel(key),
            data: data.map(row => row[key]),
            backgroundColor: this.getColor(index, 0.6),
            borderColor: this.getColor(index, 1),
            borderWidth: 2,
            fill: type === 'line' ? false : true
        }));

        new Chart(canvas, {
            type: type,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: valueKeys.length > 1,
                        position: 'top',
                    },
                    title: {
                        display: !!options.title,
                        text: options.title || ''
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.parsed.y.toLocaleString();
                                return label;
                            }
                        }
                    }
                },
                scales: type !== 'pie' ? {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                } : {}
            }
        });
    }

    /**
     * Render data table
     */
    renderTable(data, container) {
        const table = document.createElement('table');
        table.style.cssText = 'width: 100%; border-collapse: collapse;';

        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = this.formatLabel(key);
            th.style.cssText = 'padding: 12px; text-align: left; background: #f5f5f5; border-bottom: 2px solid #ddd; font-weight: 600;';
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        data.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.style.cssText = index % 2 === 0 ? 'background: #fafafa;' : 'background: white;';
            Object.values(row).forEach(value => {
                const td = document.createElement('td');
                td.textContent = typeof value === 'number' ? value.toLocaleString() : value;
                td.style.cssText = 'padding: 10px; border-bottom: 1px solid #eee;';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        container.appendChild(table);
    }

    /**
     * Render empty state
     */
    renderEmpty() {
        const div = document.createElement('div');
        div.style.cssText = 'padding: 40px; text-align: center; color: #999;';
        div.textContent = 'No data to display';
        return div;
    }

    /**
     * Format label (convert snake_case to Title Case)
     */
    formatLabel(label) {
        return label
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Get color for chart datasets
     */
    getColor(index, alpha = 1) {
        const colors = [
            `rgba(102, 126, 234, ${alpha})`,  // Purple
            `rgba(118, 75, 162, ${alpha})`,   // Deep purple
            `rgba(237, 100, 166, ${alpha})`,  // Pink
            `rgba(255, 154, 0, ${alpha})`,    // Orange
            `rgba(46, 213, 115, ${alpha})`,   // Green
            `rgba(0, 210, 255, ${alpha})`,    // Cyan
        ];
        return colors[index % colors.length];
    }
}
