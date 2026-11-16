import assert from 'node:assert/strict';
import test from 'node:test';

import { joinApiUrl } from '../src/services/apiBase.js';

test('uses the relative API path when no backend URL is configured', () => {
  const apiBase = joinApiUrl(undefined, 'api/v1');
  assert.equal(apiBase, '/api/v1');
  assert.equal(joinApiUrl(apiBase, '/auth/me'), '/api/v1/auth/me');
});

test('joins a deployed backend URL without duplicate slashes', () => {
  const apiBase = joinApiUrl('https://talentverse-api.example.com///', '/api/v1/');
  assert.equal(apiBase, 'https://talentverse-api.example.com/api/v1');
  assert.equal(
    joinApiUrl(apiBase, '//auth/me'),
    'https://talentverse-api.example.com/api/v1/auth/me',
  );
});
