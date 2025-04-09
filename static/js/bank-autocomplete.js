/**
 * Bank Autocomplete
 * A simple autocomplete implementation for bank selection.
 */
document.addEventListener('DOMContentLoaded', function() {
    const bankIdField = document.getElementById('bank_id');
    const bankSearchField = document.getElementById('bank_search');
    const bankAutocompleteResults = document.getElementById('bank-autocomplete-results');
    
    if (!bankIdField || !bankSearchField || !bankAutocompleteResults) return;
    
    // Get all bank options from the select field
    const bankOptions = Array.from(bankIdField.options).map(option => {
        return {
            id: option.value,
            name: option.text
        };
    });
    
    // Hide the original select field
    bankIdField.style.display = 'none';
    
    // Function to show autocomplete results
    function showAutocompleteResults(results) {
        // Clear previous results
        bankAutocompleteResults.innerHTML = '';
        
        if (results.length === 0) {
            bankAutocompleteResults.style.display = 'none';
            return;
        }
        
        // Create result list
        const ul = document.createElement('ul');
        ul.className = 'list-group';
        
        results.forEach(bank => {
            const li = document.createElement('li');
            li.className = 'list-group-item list-group-item-action';
            li.textContent = bank.name;
            li.dataset.id = bank.id;
            li.style.cursor = 'pointer';
            
            li.addEventListener('click', function() {
                bankIdField.value = bank.id;
                bankSearchField.value = bank.name;
                bankAutocompleteResults.style.display = 'none';
            });
            
            ul.appendChild(li);
        });
        
        bankAutocompleteResults.appendChild(ul);
        bankAutocompleteResults.style.display = 'block';
    }
    
    // Search function
    function searchBanks(query) {
        query = query.toLowerCase();
        
        if (query.length < 2) {
            bankAutocompleteResults.style.display = 'none';
            return;
        }
        
        const results = bankOptions.filter(bank => 
            bank.name.toLowerCase().includes(query)
        ).slice(0, 10); // Limit to 10 results
        
        showAutocompleteResults(results);
    }
    
    // Event listeners
    bankSearchField.addEventListener('input', function() {
        searchBanks(this.value);
    });
    
    bankSearchField.addEventListener('focus', function() {
        if (this.value.length >= 2) {
            searchBanks(this.value);
        }
    });
    
    // Close autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== bankSearchField && e.target !== bankAutocompleteResults) {
            bankAutocompleteResults.style.display = 'none';
        }
    });
    
    // If bank_id has a value, find and display the bank name
    if (bankIdField.value) {
        const selectedBank = bankOptions.find(bank => bank.id == bankIdField.value);
        if (selectedBank) {
            bankSearchField.value = selectedBank.name;
        }
    }
});