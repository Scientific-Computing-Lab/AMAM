(() => {
  function encodePathSegment(segment) {
    return encodeURIComponent(segment).replace(
      /[!'()*]/g,
      char => `%${char.charCodeAt(0).toString(16).toUpperCase()}`
    );
  }

  function anonymousRepoId(pathname) {
    const match = String(pathname || "").match(/^\/w\/([^/]+)(?:\/|$)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  function toAssetUrl(path, pathname = window.location.pathname) {
    if (!path) {
      return path;
    }

    const value = String(path);
    if (/^(?:[a-z][a-z\d+.-]*:|\/\/|\/|#)/i.test(value)) {
      return value;
    }

    const repoId = anonymousRepoId(pathname);
    if (!repoId) {
      return encodeURI(value);
    }

    const encodedPath = value.split("/").map(encodePathSegment).join("/");
    return `/api/repo/${encodeURIComponent(repoId)}/file/${encodedPath}`;
  }

  window.AmamAssetUrl = Object.freeze({ toAssetUrl });
})();
