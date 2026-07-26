import axios from "axios";

const api = axios.create({
    baseURL: "http://127.0.0.1:8000/api",
    timeout: 30000,
});

export default api;

export const getTickers = () =>
    api.get("/tickers");

export const getPrice = (ticker) =>
    api.get(`/price/${ticker}`);

export const getSignal = (ticker) =>
    api.get(`/signal/${ticker}`);

export const getSentiment = (ticker) =>
    api.get(`/sentiment/${ticker}`);

export const getDashboard = (ticker) =>
    api.get(`/dashboard/${ticker}`);

export const getModelResults = () =>
    api.get("/model-results");