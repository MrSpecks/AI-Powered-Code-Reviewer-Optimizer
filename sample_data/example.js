/**
 * Example JavaScript file for testing the code reviewer.
 * Contains various functions and patterns for analysis.
 */

// Global variables (not recommended)
var globalCounter = 0;

// Function with potential issues
function calculateTotal(items) {
    var total = 0;
    for (var i = 0; i < items.length; i++) {
        total += items[i].price;
    }
    return total;
}

// Arrow function with modern syntax
const calculateTax = (amount, rate) => {
    return amount * rate;
};

// Async function
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.log('Error fetching user data:', error);
        return null;
    }
}

// Class definition
class UserManager {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        if (user && user.name) {
            this.users.push(user);
        }
    }
    
    findUser(id) {
        return this.users.find(user => user.id == id);
    }
    
    getAllUsers() {
        return this.users;
    }
}

// Object with methods
const utils = {
    formatDate: function(date) {
        return date.toISOString().split('T')[0];
    },
    
    validateEmail: function(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    },
    
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        calculateTotal,
        calculateTax,
        fetchUserData,
        UserManager,
        utils
    };
}
