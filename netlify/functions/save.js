exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  try {
    const { path, data } = JSON.parse(event.body);
    const token = process.env.GITHUB_TOKEN;
    const user  = process.env.GITHUB_USER;
    const repo  = process.env.GITHUB_REPO;

    if (!token || !user || !repo) {
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'Variables de entorno no configuradas' }),
      };
    }

    const url = `https://api.github.com/repos/${user}/${repo}/contents/${path}`;

    const actual = await fetch(url, {
      headers: { 'Authorization': `token ${token}` },
    }).then(r => r.json());

    const res = await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': `token ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `StudyES: actualizar ${path}`,
        content: btoa(unescape(encodeURIComponent(
          JSON.stringify(data, null, 2)
        ))),
        sha: actual.sha,
        branch: process.env.GITHUB_BRANCH || 'main',
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return {
        statusCode: res.status,
        body: JSON.stringify({ error: err.message || 'GitHub API error' }),
      };
    }

    return { statusCode: 200, body: JSON.stringify({ ok: true }) };

  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message }),
    };
  }
};
