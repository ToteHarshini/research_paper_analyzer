/**
 * API Service for the Research Paper Analyzer
 * Handles communication with the FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Check backend health and configuration status.
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    return {
      status: 'unreachable',
      version: 'unknown',
      llm_provider: null,
      database_connected: false,
      error: error.message,
    };
  }
}

/**
 * Submit a research question and multiple PDF files for agentic analysis.
 * Uses FormData as required by the backend multipart/form-data endpoint.
 *
 * @param {string} question - The research question.
 * @param {File[]} files - Array of PDF File objects.
 * @returns {Promise<Object>} The synthesized research analysis result.
 */
export async function analyzePapers(question, files) {
  if (!question || !question.trim()) {
    throw new Error('Research question cannot be empty.');
  }

  if (!files || files.length === 0) {
    throw new Error('Please select at least one PDF research paper.');
  }

  const formData = new FormData();
  formData.append('question', question.trim());

  for (const file of files) {
    formData.append('files', file);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
    });
  } catch (networkError) {
    throw new Error(
      `Unable to reach backend server at ${API_BASE_URL}. Ensure FastAPI is running on port 8000.`
    );
  }

  if (!response.ok) {
    let errorDetail = 'Analysis request failed.';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (_) {
      errorDetail = `Server responded with status ${response.status}`;
    }
    throw new Error(errorDetail);
  }

  return await response.json();
}

/**
 * Send a follow-up question using the analyzed paper context and evidence.
 *
 * @param {Object} payload
 * @param {string} payload.question - Follow-up question.
 * @param {string} [payload.context] - Prior research report summary.
 * @param {Array} [payload.evidence] - Retrieved paper passages.
 * @param {Array} [payload.history] - Conversation history.
 * @returns {Promise<Object>} Chat answer and sources.
 */
export async function sendChatMessage({ question, context, evidence, history }) {
  if (!question || !question.trim()) {
    throw new Error('Follow-up question cannot be empty.');
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question.trim(),
        context: context || null,
        evidence: evidence || null,
        history: history || null,
      }),
    });
  } catch (networkError) {
    throw new Error(
      `Unable to reach backend server at ${API_BASE_URL}. Ensure FastAPI is running.`
    );
  }

  if (!response.ok) {
    let errorDetail = 'Follow-up chat request failed.';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch (_) {
      errorDetail = `Server responded with status ${response.status}`;
    }
    throw new Error(errorDetail);
  }

  return await response.json();
}
