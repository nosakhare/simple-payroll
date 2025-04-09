/**
 * Nigerian Payroll System - Chart Configuration
 * 
 * This file contains chart configurations for the dashboard and reports.
 */

// Helper for working with colors
const chartColors = {
    primary: '#0d6efd',
    secondary: '#6c757d',
    success: '#20c997',
    info: '#0dcaf0',
    warning: '#ffc107',
    danger: '#dc3545',
    light: '#f8f9fa',
    dark: '#212529',
    primaryLight: '#6ea8fe',
    secondaryLight: '#a7acb1',
    successLight: '#6edcb8',
    infoLight: '#6edcf5',
    warningLight: '#ffda6a',
    dangerLight: '#ea868f',
    // Add transparency
    transparent: (color, alpha = 0.2) => {
        // For hex colors
        if (color.startsWith('#')) {
            const r = parseInt(color.slice(1, 3), 16);
            const g = parseInt(color.slice(3, 5), 16);
            const b = parseInt(color.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        // For rgb colors
        if (color.startsWith('rgb(')) {
            const rgb = color.match(/\d+/g);
            return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
        }
        return color;
    }
};

/**
 * Configure the payroll distribution chart on the dashboard
 * @param {HTMLElement} chartElement - The chart canvas element
 * @param {Object} data - The data for the chart
 */
function configurePayrollDistributionChart(chartElement, data = null) {
    if (!chartElement) return;
    
    // Default data if none provided
    const chartData = data || {
        basicSalary: 60,
        allowances: 30,
        tax: 8,
        otherDeductions: 2
    };
    
    new Chart(chartElement.getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Basic Salary', 'Allowances', 'Tax', 'Other Deductions'],
            datasets: [{
                data: [
                    chartData.basicSalary,
                    chartData.allowances,
                    chartData.tax,
                    chartData.otherDeductions
                ],
                backgroundColor: [
                    chartColors.primary,
                    chartColors.success,
                    chartColors.danger,
                    chartColors.secondary
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#f8f9fa'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${value}%`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Configure the monthly payroll trend chart
 * @param {HTMLElement} chartElement - The chart canvas element
 * @param {Object} data - The data for the chart
 */
function configurePayrollTrendChart(chartElement, data = null) {
    if (!chartElement) return;
    
    // Default data if none provided
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const chartData = data || {
        labels: months.slice(0, 6), // Last 6 months
        datasets: {
            totalBasic: [4500000, 4600000, 4700000, 4750000, 4800000, 4850000],
            totalNet: [3800000, 3900000, 4000000, 4050000, 4100000, 4150000]
        }
    };
    
    new Chart(chartElement.getContext('2d'), {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Total Basic Salary',
                    data: chartData.datasets.totalBasic,
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.transparent(chartColors.primary, 0.2),
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Total Net Pay',
                    data: chartData.datasets.totalNet,
                    borderColor: chartColors.success,
                    backgroundColor: chartColors.transparent(chartColors.success, 0.2),
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: chartColors.transparent(chartColors.light, 0.1)
                    },
                    ticks: {
                        color: chartColors.light
                    }
                },
                y: {
                    grid: {
                        color: chartColors.transparent(chartColors.light, 0.1)
                    },
                    ticks: {
                        color: chartColors.light,
                        callback: function(value) {
                            return '₦' + value.toLocaleString('en-NG');
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: chartColors.light
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            return `${label}: ₦${value.toLocaleString('en-NG')}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Configure the department distribution chart
 * @param {HTMLElement} chartElement - The chart canvas element
 * @param {Object} data - The data for the chart
 */
function configureDepartmentChart(chartElement, data = null) {
    if (!chartElement) return;
    
    // Default data if none provided
    const chartData = data || {
        labels: ['IT', 'HR', 'Finance', 'Marketing', 'Operations', 'Sales'],
        datasets: {
            employeeCount: [12, 8, 10, 15, 20, 18],
            totalSalary: [4800000, 3200000, 5000000, 6000000, 8000000, 7200000]
        }
    };
    
    new Chart(chartElement.getContext('2d'), {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Employee Count',
                    data: chartData.datasets.employeeCount,
                    backgroundColor: chartColors.transparent(chartColors.primary, 0.8),
                    borderColor: chartColors.primary,
                    borderWidth: 1,
                    borderRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'Total Salary (₦)',
                    data: chartData.datasets.totalSalary,
                    backgroundColor: chartColors.transparent(chartColors.success, 0.8),
                    borderColor: chartColors.success,
                    borderWidth: 1,
                    borderRadius: 4,
                    type: 'line',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: chartColors.transparent(chartColors.light, 0.1)
                    },
                    ticks: {
                        color: chartColors.light
                    }
                },
                y: {
                    grid: {
                        color: chartColors.transparent(chartColors.light, 0.1)
                    },
                    ticks: {
                        color: chartColors.light
                    },
                    title: {
                        display: true,
                        text: 'Employee Count',
                        color: chartColors.light
                    }
                },
                y1: {
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: chartColors.light,
                        callback: function(value) {
                            return '₦' + (value / 1000000).toFixed(1) + 'M';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Total Salary',
                        color: chartColors.light
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: chartColors.light
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            
                            if (label.includes('Employee')) {
                                return `${label}: ${value}`;
                            } else {
                                return `${label}: ₦${value.toLocaleString('en-NG')}`;
                            }
                        }
                    }
                }
            }
        }
    });
}

// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Payroll Distribution Chart on Dashboard
    const payrollDistributionChart = document.getElementById('payrollDistribution');
    if (payrollDistributionChart) {
        configurePayrollDistributionChart(payrollDistributionChart);
    }
    
    // Other charts can be initialized here when needed
});
