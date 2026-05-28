const accountTypeField = document.getElementById('id_account_type');
const businessNameWrapper = document.getElementById('div_id_business_name');
const businessNameInput = document.getElementById('id_business_name');

function toggleBusinessNameField() {
    if (!accountTypeField || !businessNameWrapper) {
        return;
    }

    if (accountTypeField.value === 'provider') {
        businessNameWrapper.style.display = 'block';
    } else {
        businessNameWrapper.style.display = 'none';

        if (businessNameInput) {
            businessNameInput.value = '';
        }
    }
}

toggleBusinessNameField();

accountTypeField.addEventListener('change', toggleBusinessNameField);
