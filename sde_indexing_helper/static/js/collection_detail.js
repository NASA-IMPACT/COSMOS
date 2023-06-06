let originalValue = document.getElementById('github-link-display').textContent;
document.getElementById('github-link-form').style.display = 'none';
document.getElementById('cancel-github-link-button').style.display = 'none';
document.getElementById('edit-github-link-button').addEventListener('click', function() {
    document.getElementById('id_github_issue_link').value = originalValue;
    document.getElementById('cancel-github-link-button').style.display = 'block';
    document.getElementById('edit-github-link-button').style.display = 'none';
    document.getElementById('github-link-display').style.display = 'none';
    document.getElementById('github-link-form').style.display = 'block';
});

document.getElementById('cancel-github-link-button').addEventListener('click', function() {
    document.getElementById('cancel-github-link-button').style.display = 'none';
    document.getElementById('edit-github-link-button').style.display = 'block';
    document.getElementById('github-link-display').style.display = 'block';
    document.getElementById('github-link-form').style.display = 'none';
    document.getElementById('id_github_issue_link').value = originalValue;
});
