async function login() {
    let loginButton = $('#loginButton')
    loginButton.prop('disabled', true)

    let data = getValues('#data-items')

    try {
        let response = await fetch(`/admin/login/`, {
            method: 'POST',
            body: JSON.stringify({
                ...data
            })
        });

        response = await response.json();
        if (response._success === true) {
            location.href = '/api/';
        } else {
            alert(response.message);
            loginButton.prop('disabled', false)
        }

    } catch (error) {
        alert(`${error.message}`);
        loginButton.prop('disabled', false)
    }
}

$(document).on('keypress', async function (e) {
    if (e.which === 13) {
        await login();
    }
});

