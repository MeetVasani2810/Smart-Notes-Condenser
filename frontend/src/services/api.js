/**
 * api.js
 * -------
 * Axios service for communicating with the FastAPI backend.
 *
 * All backend calls are centralised here so that if the API URL changes,
 * only this file needs to be updated.
 */

import axios from "axios";

// Backend base URL — FastAPI running on port 8000
const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  // Timeout after 300 seconds — quiz/flashcards make up to 10 model calls
  timeout: 300000,
});

/**
 * Send study notes to the backend for processing.
 *
 * @param {string} text   - Student's study notes
 * @param {string} task   - "summary" | "key_points" | "quiz" | "flashcards"
 * @returns {Promise<{result: string}>}
 */
export async function generateContent(text, task) {
  const response = await api.post("/generate", { text, task });
  return response.data;
}

/**
 * Check if the backend is running and the model is loaded.
 *
 * @returns {Promise<{status: string, model_loaded: boolean}>}
 */
export async function checkHealth() {
  const response = await api.get("/health");
  return response.data;
}
