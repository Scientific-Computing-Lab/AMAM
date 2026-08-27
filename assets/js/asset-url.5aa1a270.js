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

  // Full-repository archive for the host currently serving the page. The
  // anonymous host streams its own zip, so the download stays anonymous and
  // costs one request instead of one per file. Derived from location rather
  // than stored in the repo, so no upstream URL is published in the metadata.
  function toRepoZipUrl(
    pathname = window.location.pathname,
    hostname = window.location.hostname
  ) {
    const repoId = anonymousRepoId(pathname);
    if (repoId) {
      return `/api/repo/${encodeURIComponent(repoId)}/zip`;
    }

    const pagesOwner = String(hostname || "").match(/^([^.]+)\.github\.io$/i);
    const pagesRepo = String(pathname || "").split("/").filter(Boolean)[0];
    if (pagesOwner && pagesRepo) {
      return (
        `https://github.com/${encodePathSegment(pagesOwner[1])}/` +
        `${encodePathSegment(pagesRepo)}/archive/refs/heads/main.zip`
      );
    }

    return null;
  }

  window.AmamAssetUrl = Object.freeze({ toAssetUrl, toRepoZipUrl });
})();
