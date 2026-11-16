export function joinApiUrl(baseUrl, path) {
  const normalizedBase = (baseUrl || '').trim().replace(/\/+$/, '');
  const normalizedPath = path.trim().replace(/^\/+|\/+$/g, '');
  return normalizedBase ? `${normalizedBase}/${normalizedPath}` : `/${normalizedPath}`;
}
